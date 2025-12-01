param(
    [string]$SubscriptionId,
    [string]$Location = "eastus",
    [string]$ResourceGroupName = "pubsec-terraform-state-rg",
    [string]$StorageAccountName = "pubsecterraformstate",
    [string]$ContainerName = "tfstate",
    [switch]$AutoSuffixIfTaken
)

Write-Host "Bootstrapping Terraform remote state in Azure..." -ForegroundColor Cyan

# Ensure Azure CLI is available
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI (az) not found. Install from https://aka.ms/installazurecliwindows"
    exit 1
}

# Login if needed
try {
    $account = az account show --output json | ConvertFrom-Json
} catch {
    Write-Host "Running 'az login'..." -ForegroundColor Yellow
    az login | Out-Null
}

if ($SubscriptionId) {
    az account set --subscription $SubscriptionId | Out-Null
}

# Create resource group
Write-Host "Ensuring resource group '$ResourceGroupName' in '$Location'..." -ForegroundColor Cyan
az group create --name $ResourceGroupName --location $Location --output none

# Storage account names must be globally unique and 3-24 lowercase alphanumerics
$saName = $StorageAccountName.ToLower()
$isAvailable = az storage account check-name --name $saName --query "nameAvailable" -o tsv 2>$null
if ($isAvailable -eq "false") {
        if ($AutoSuffixIfTaken) {
                $base = $saName
                # Trim base if needed to allow suffix up to 6 chars
                if ($base.Length -gt 18) { $base = $base.Substring(0, 18) }
                $suffix = -join ((48..57 + 97..122) | Get-Random -Count 6 | ForEach-Object {[char]$_})
                $saName = "$base$suffix"
                Write-Host "Original storage account name unavailable. Using '$saName'" -ForegroundColor Yellow
        } else {
                Write-Error "Storage account name '$saName' is not available. Re-run with -AutoSuffixIfTaken or provide a different -StorageAccountName."
                exit 1
        }
}

Write-Host "Ensuring storage account '$saName'..." -ForegroundColor Cyan
az storage account create `
    --name $saName `
    --resource-group $ResourceGroupName `
    --location $Location `
    --sku Standard_LRS `
    --kind StorageV2 `
    --min-tls-version TLS1_2 `
    --allow-blob-public-access false `
    --output none

# Get storage account key
$key = az storage account keys list --resource-group $ResourceGroupName --account-name $saName --query "[0].value" -o tsv
if (-not $key) {
    Write-Error "Failed to retrieve storage account key for '$StorageAccountName'"
    exit 1
}

# Create container if not exists
Write-Host "Ensuring blob container '$ContainerName'..." -ForegroundColor Cyan
az storage container create `
    --name $ContainerName `
    --account-name $saName `
    --account-key $key `
    --public-access off `
    --output none

Write-Host "Remote state ready." -ForegroundColor Green
Write-Host "Backend settings (match terraform backend block):" -ForegroundColor Gray
Write-Host "  resource_group_name  = $ResourceGroupName"
Write-Host "  storage_account_name = $saName"
Write-Host "  container_name       = $ContainerName"
Write-Host "  key                  = pubsec-info-assistant.tfstate"

Write-Host "Next: terraform init -reconfigure" -ForegroundColor Green
Write-Host "Alternatively use -backend-config overrides:" -ForegroundColor Gray
Write-Host "  terraform init -reconfigure `\" -backend-config=resource_group_name=$ResourceGroupName `\" -backend-config=storage_account_name=$saName `\" -backend-config=container_name=$ContainerName `\" -backend-config=key=pubsec-info-assistant.tfstate"
