<#
.SYNOPSIS
    Automated T-Shirt Sized Deployment for EVA Domain Assistant 2.0 on Azure

.DESCRIPTION
    This script automates the deployment of EVA Domain Assistant 2.0 to Azure using
    predefined t-shirt sizes (XS, S, M, L). It handles Terraform initialization,
    configuration, validation, and deployment with the appropriate parameters for
    each size.

.PARAMETER Size
    T-shirt size for deployment: XS (Demo), S (Dev), M (Production), L (Enterprise)

.PARAMETER Environment
    Environment name (e.g., demo, dev, staging, production)

.PARAMETER Location
    Azure region for deployment (default: eastus)

.PARAMETER Owner
    Owner email address for resource tagging

.PARAMETER OpenAIKey
    OpenAI API key (required). Can also be set via $env:TF_VAR_openai_api_key

.PARAMETER ResourceGroupName
    Custom resource group name (optional). If not provided, uses: pubsec-info-assistant-{environment}-rg

.PARAMETER SkipValidation
    Skip pre-deployment validation checks

.PARAMETER AutoApprove
    Automatically approve Terraform apply without prompting

.PARAMETER EnableDDoS
    Enable DDoS Protection Standard (adds ~$3000/month, recommended for production)

.PARAMETER EnablePrivateCluster
    Enable private AKS cluster (recommended for production)

.PARAMETER EnableMultiRegion
    Enable multi-region geo-replication for ACR (Size M and L)

.PARAMETER SecondaryRegion
    Secondary Azure region for geo-replication (default: westus2)

.PARAMETER DryRun
    Preview changes without applying (terraform plan only)

.PARAMETER Destroy
    Destroy the infrastructure instead of creating it

.EXAMPLE
    .\deploy-tshirt.ps1 -Size XS -Environment demo -Location eastus -Owner "demo@example.com" -OpenAIKey "sk-..."
    Deploy Size XS (Demo) configuration

.EXAMPLE
    .\deploy-tshirt.ps1 -Size M -Environment production -EnableDDoS -EnablePrivateCluster -AutoApprove
    Deploy Size M (Production) with DDoS protection and private cluster

.EXAMPLE
    .\deploy-tshirt.ps1 -Size L -Environment production -EnableMultiRegion -SecondaryRegion westus2
    Deploy Size L (Enterprise) with multi-region geo-replication

.EXAMPLE
    .\deploy-tshirt.ps1 -Size S -Environment dev -DryRun
    Preview Size S deployment without applying changes

.EXAMPLE
    .\deploy-tshirt.ps1 -Size M -Environment production -Destroy
    Destroy Size M production infrastructure

.NOTES
    Version: 1.0.0
    Author: DevOps/SRE Team
    Last Updated: 2025-11-30
    Requires: Azure CLI 2.50+, Terraform 1.5+, PowerShell 7.0+
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("XS", "S", "M", "L")]
    [string]$Size,

    [Parameter(Mandatory = $true)]
    [string]$Environment,

    [Parameter(Mandatory = $false)]
    [string]$Location = "eastus",

    [Parameter(Mandatory = $false)]
    [string]$Owner,

    [Parameter(Mandatory = $false)]
    [string]$OpenAIKey,

    [Parameter(Mandatory = $false)]
    [string]$ResourceGroupName,

    [Parameter(Mandatory = $false)]
    [switch]$SkipValidation,

    [Parameter(Mandatory = $false)]
    [switch]$AutoApprove,

    [Parameter(Mandatory = $false)]
    [switch]$EnableDDoS,

    [Parameter(Mandatory = $false)]
    [switch]$EnablePrivateCluster,

    [Parameter(Mandatory = $false)]
    [switch]$EnableMultiRegion,

    [Parameter(Mandatory = $false)]
    [string]$SecondaryRegion = "westus2",

    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [switch]$Destroy
)

# =============================================================================
# Configuration
# =============================================================================

$ErrorActionPreference = "Stop"
$WarningPreference = "Continue"

$script:ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:TerraformDir = Split-Path -Parent $script:ScriptDir
$script:EnvironmentsDir = Join-Path $script:TerraformDir "environments"

# T-shirt size configurations
$script:TShirtConfigs = @{
    XS = @{
        Name         = "Extra Small (Demo/POC)"
        Users        = "1-10"
        MonthlyCost  = "$150-300"
        SetupTime    = "20 minutes"
        SLA          = "99.5%"
        Description  = "Proof of concept, demos, testing, small pilots"
    }
    S  = @{
        Name         = "Small (Development)"
        Users        = "10-50"
        MonthlyCost  = "$400-600"
        SetupTime    = "30 minutes"
        SLA          = "99.9%"
        Description  = "Development, staging, QA testing, small production workloads"
    }
    M  = @{
        Name         = "Medium (Production)"
        Users        = "50-500"
        MonthlyCost  = "$1,500-2,500 (without DDoS)"
        SetupTime    = "45 minutes"
        SLA          = "99.95%"
        Description  = "Production workloads, business-critical applications"
    }
    L  = @{
        Name         = "Large (Multi-Tenant Enterprise)"
        Users        = "500-5000+"
        MonthlyCost  = "$10,000-15,000"
        SetupTime    = "60 minutes"
        SLA          = "99.99%"
        Description  = "Multi-tenant SaaS, enterprise-scale, government-wide deployments"
    }
}

# =============================================================================
# Helper Functions
# =============================================================================

function Write-Banner {
    param([string]$Message)
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host "→ $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "  $Message" -ForegroundColor Gray
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-ErrorMessage {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Test-AzureCLI {
    if (-not (Test-Command "az")) {
        Write-ErrorMessage "Azure CLI not found. Please install: https://aka.ms/azure-cli"
        return $false
    }

    $azVersion = (az version --output json | ConvertFrom-Json).'azure-cli'
    Write-Info "Azure CLI version: $azVersion"

    # Check if logged in
    try {
        $account = az account show 2>$null | ConvertFrom-Json
        if ($null -eq $account) {
            Write-ErrorMessage "Not logged in to Azure. Run: az login"
            return $false
        }
        Write-Info "Logged in as: $($account.user.name)"
        Write-Info "Subscription: $($account.name) ($($account.id))"
        return $true
    }
    catch {
        Write-ErrorMessage "Not logged in to Azure. Run: az login"
        return $false
    }
}

function Test-Terraform {
    if (-not (Test-Command "terraform")) {
        Write-ErrorMessage "Terraform not found. Please install: https://www.terraform.io/downloads"
        return $false
    }

    $tfVersion = (terraform version -json | ConvertFrom-Json).terraform_version
    Write-Info "Terraform version: $tfVersion"

    # Check minimum version (1.5.0)
    $minVersion = [Version]"1.5.0"
    $currentVersion = [Version]$tfVersion
    if ($currentVersion -lt $minVersion) {
        Write-ErrorMessage "Terraform version $tfVersion is too old. Minimum required: 1.5.0"
        return $false
    }

    return $true
}

function Test-Prerequisites {
    Write-Step "Validating prerequisites..."

    $allValid = $true

    # Check PowerShell version
    if ($PSVersionTable.PSVersion.Major -lt 7) {
        Write-ErrorMessage "PowerShell 7.0+ required. Current: $($PSVersionTable.PSVersion)"
        $allValid = $false
    }
    else {
        Write-Info "PowerShell version: $($PSVersionTable.PSVersion)"
    }

    # Check Azure CLI
    if (-not (Test-AzureCLI)) {
        $allValid = $false
    }

    # Check Terraform
    if (-not (Test-Terraform)) {
        $allValid = $false
    }

    return $allValid
}

function Get-TerraformStateConfig {
    Write-Step "Checking Terraform state backend..."

    # Check if state backend exists
    $stateRG = "pubsec-terraform-state-rg"
    $stateSA = "pubsecterraformstate"
    $stateContainer = "tfstate"

    try {
        $rgExists = az group exists --name $stateRG | ConvertFrom-Json
        if (-not $rgExists) {
            Write-Warning "Terraform state resource group not found: $stateRG"
            Write-Info "Creating Terraform state backend..."

            # Create resource group
            az group create --name $stateRG --location $Location | Out-Null
            Write-Success "Created resource group: $stateRG"

            # Create storage account
            az storage account create `
                --name $stateSA `
                --resource-group $stateRG `
                --location $Location `
                --sku Standard_LRS `
                --encryption-services blob `
                --allow-blob-public-access false | Out-Null
            Write-Success "Created storage account: $stateSA"

            # Create container
            az storage container create `
                --name $stateContainer `
                --account-name $stateSA `
                --auth-mode login | Out-Null
            Write-Success "Created blob container: $stateContainer"
        }
        else {
            Write-Success "Terraform state backend exists"
        }
    }
    catch {
        Write-ErrorMessage "Failed to create Terraform state backend: $_"
        return $false
    }

    return @{
        ResourceGroup  = $stateRG
        StorageAccount = $stateSA
        Container      = $stateContainer
        Key            = "$Environment.tfstate"
    }
}

function Initialize-Terraform {
    param([hashtable]$StateConfig)

    Write-Step "Initializing Terraform..."

    Push-Location $script:TerraformDir

    try {
        # Remove existing .terraform directory to ensure clean init
        if (Test-Path ".terraform") {
            Write-Info "Removing existing .terraform directory..."
            Remove-Item -Recurse -Force ".terraform"
        }

        # Initialize with backend configuration
        $initArgs = @(
            "init",
            "-reconfigure",
            "-backend-config=`"resource_group_name=$($StateConfig.ResourceGroup)`"",
            "-backend-config=`"storage_account_name=$($StateConfig.StorageAccount)`"",
            "-backend-config=`"container_name=$($StateConfig.Container)`"",
            "-backend-config=`"key=$($StateConfig.Key)`""
        )

        $initCmd = "terraform $($initArgs -join ' ')"
        Write-Info "Running: $initCmd"

        & terraform @initArgs

        if ($LASTEXITCODE -ne 0) {
            throw "Terraform init failed with exit code $LASTEXITCODE"
        }

        Write-Success "Terraform initialized successfully"
        return $true
    }
    catch {
        Write-ErrorMessage "Terraform initialization failed: $_"
        return $false
    }
    finally {
        Pop-Location
    }
}

function New-TerraformVars {
    param(
        [string]$Size,
        [string]$Environment,
        [string]$Location,
        [string]$Owner,
        [string]$OpenAIKey
    )

    Write-Step "Generating Terraform variables..."

    # Base tfvars file for the size
    $baseTfvars = Join-Path $script:EnvironmentsDir "$($Size.ToLower()).tfvars"
    if (-not (Test-Path $baseTfvars)) {
        Write-ErrorMessage "T-shirt size configuration not found: $baseTfvars"
        return $null
    }

    # Create custom tfvars file with overrides
    $customTfvars = Join-Path $script:EnvironmentsDir "custom-$Environment.tfvars"

    # Read base configuration
    $baseContent = Get-Content $baseTfvars -Raw

    # Apply overrides
    $overrides = @"

# =============================================================================
# Custom Overrides (Generated by deploy-tshirt.ps1)
# =============================================================================
# Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# Size: $Size
# Environment: $Environment
# =============================================================================

environment = "$Environment"
location    = "$Location"
"@

    if ($Owner) {
        $overrides += "`nowner       = `"$Owner`""
    }

    # Size-specific overrides
    if ($EnableDDoS -and ($Size -eq "M" -or $Size -eq "L")) {
        $overrides += "`nenable_ddos_protection = true"
    }

    if ($EnablePrivateCluster -and ($Size -ne "XS")) {
        $overrides += "`naks_enable_private_cluster = true"
    }

    if ($EnableMultiRegion -and ($Size -eq "M" -or $Size -eq "L")) {
        $overrides += "`nacr_geo_replication_locations = [`"$SecondaryRegion`"]"
    }

    # Write custom tfvars
    $baseContent + $overrides | Set-Content -Path $customTfvars -NoNewline

    Write-Success "Generated custom configuration: $customTfvars"

    return $customTfvars
}

function Invoke-TerraformPlan {
    param([string]$TfvarsFile)

    Write-Step "Planning Terraform deployment..."

    Push-Location $script:TerraformDir

    try {
        $planArgs = @(
            "plan",
            "-var-file=`"$TfvarsFile`"",
            "-out=tfplan"
        )

        # Add OpenAI key if provided
        if ($OpenAIKey) {
            $env:TF_VAR_openai_api_key = $OpenAIKey
        }

        Write-Info "Running: terraform $($planArgs -join ' ')"

        & terraform @planArgs

        if ($LASTEXITCODE -ne 0) {
            throw "Terraform plan failed with exit code $LASTEXITCODE"
        }

        Write-Success "Terraform plan completed successfully"
        return $true
    }
    catch {
        Write-ErrorMessage "Terraform plan failed: $_"
        return $false
    }
    finally {
        Pop-Location
    }
}

function Invoke-TerraformApply {
    param([bool]$AutoApprove)

    Write-Step "Applying Terraform deployment..."

    Push-Location $script:TerraformDir

    try {
        $applyArgs = @("apply")

        if ($AutoApprove) {
            $applyArgs += "-auto-approve"
        }

        $applyArgs += "tfplan"

        Write-Info "Running: terraform $($applyArgs -join ' ')"

        & terraform @applyArgs

        if ($LASTEXITCODE -ne 0) {
            throw "Terraform apply failed with exit code $LASTEXITCODE"
        }

        Write-Success "Terraform deployment completed successfully"
        return $true
    }
    catch {
        Write-ErrorMessage "Terraform apply failed: $_"
        return $false
    }
    finally {
        Pop-Location
    }
}

function Invoke-TerraformDestroy {
    param([string]$TfvarsFile, [bool]$AutoApprove)

    Write-Step "Destroying Terraform infrastructure..."

    Push-Location $script:TerraformDir

    try {
        $destroyArgs = @(
            "destroy",
            "-var-file=`"$TfvarsFile`""
        )

        if ($AutoApprove) {
            $destroyArgs += "-auto-approve"
        }

        # Add OpenAI key if provided
        if ($OpenAIKey) {
            $env:TF_VAR_openai_api_key = $OpenAIKey
        }

        Write-Warning "This will DESTROY all resources in $Environment environment!"
        if (-not $AutoApprove) {
            $confirm = Read-Host "Type 'yes' to confirm destruction"
            if ($confirm -ne "yes") {
                Write-Info "Destruction cancelled"
                return $false
            }
        }

        Write-Info "Running: terraform $($destroyArgs -join ' ')"

        & terraform @destroyArgs

        if ($LASTEXITCODE -ne 0) {
            throw "Terraform destroy failed with exit code $LASTEXITCODE"
        }

        Write-Success "Infrastructure destroyed successfully"
        return $true
    }
    catch {
        Write-ErrorMessage "Terraform destroy failed: $_"
        return $false
    }
    finally {
        Pop-Location
    }
}

function Show-DeploymentSummary {
    param([string]$Size, [string]$Environment, [string]$Location)

    $config = $script:TShirtConfigs[$Size]

    Write-Banner "Deployment Summary"

    Write-Host "Configuration:"
    Write-Host "  Size:          $Size - $($config.Name)" -ForegroundColor Cyan
    Write-Host "  Environment:   $Environment" -ForegroundColor Cyan
    Write-Host "  Location:      $Location" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Specifications:"
    Write-Host "  Users:         $($config.Users)"
    Write-Host "  Monthly Cost:  $($config.MonthlyCost)"
    Write-Host "  Setup Time:    $($config.SetupTime)"
    Write-Host "  SLA:           $($config.SLA)"
    Write-Host "  Description:   $($config.Description)"
    Write-Host ""

    if ($EnableDDoS) {
        Write-Host "  DDoS Protection:     Enabled (+$3,000/month)" -ForegroundColor Yellow
    }
    if ($EnablePrivateCluster) {
        Write-Host "  Private Cluster:     Enabled" -ForegroundColor Yellow
    }
    if ($EnableMultiRegion) {
        Write-Host "  Multi-Region:        Enabled ($SecondaryRegion)" -ForegroundColor Yellow
    }

    Write-Host ""
}

function Show-NextSteps {
    param([string]$Environment)

    Write-Banner "Next Steps"

    Write-Host "1. Get AKS credentials:"
    Write-Host "   az aks get-credentials --resource-group pubsec-info-assistant-$Environment-rg --name pubsec-info-assistant-$Environment-aks" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "2. Verify cluster:"
    Write-Host "   kubectl get nodes" -ForegroundColor Yellow
    Write-Host "   kubectl get pods --all-namespaces" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "3. Deploy application:"
    Write-Host "   cd ../k8s" -ForegroundColor Yellow
    Write-Host "   kubectl apply -k overlays/$Environment/" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "4. Monitor deployment:"
    Write-Host "   kubectl get pods -w" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "5. View outputs:"
    Write-Host "   terraform output" -ForegroundColor Yellow
    Write-Host ""
}

# =============================================================================
# Main Script
# =============================================================================

function Main {
    Write-Banner "EVA Domain Assistant 2.0 - T-Shirt Sized Deployment"

    # Show deployment configuration
    Show-DeploymentSummary -Size $Size -Environment $Environment -Location $Location

    # Validate prerequisites
    if (-not $SkipValidation) {
        if (-not (Test-Prerequisites)) {
            Write-ErrorMessage "Prerequisites validation failed. Fix issues and try again."
            exit 1
        }
        Write-Success "Prerequisites validated"
        Write-Host ""
    }

    # Validate OpenAI key
    if (-not $OpenAIKey -and -not $env:TF_VAR_openai_api_key) {
        Write-ErrorMessage "OpenAI API key required. Use -OpenAIKey or set `$env:TF_VAR_openai_api_key"
        exit 1
    }

    # Set default owner if not provided
    if (-not $Owner) {
        try {
            $azAccount = az account show | ConvertFrom-Json
            $Owner = $azAccount.user.name
            Write-Info "Using Azure account email as owner: $Owner"
        }
        catch {
            Write-Warning "Could not determine owner from Azure account"
            $Owner = "unknown@example.com"
        }
    }

    # Configure Terraform state backend
    $stateConfig = Get-TerraformStateConfig
    if (-not $stateConfig) {
        Write-ErrorMessage "Failed to configure Terraform state backend"
        exit 1
    }
    Write-Host ""

    # Initialize Terraform
    if (-not (Initialize-Terraform -StateConfig $stateConfig)) {
        Write-ErrorMessage "Terraform initialization failed"
        exit 1
    }
    Write-Host ""

    # Handle destroy operation
    if ($Destroy) {
        $tfvarsFile = New-TerraformVars `
            -Size $Size `
            -Environment $Environment `
            -Location $Location `
            -Owner $Owner `
            -OpenAIKey $OpenAIKey

        if (-not $tfvarsFile) {
            exit 1
        }

        if (Invoke-TerraformDestroy -TfvarsFile $tfvarsFile -AutoApprove $AutoApprove) {
            Write-Banner "Destruction Complete"
            Write-Success "Infrastructure destroyed successfully"
        }
        else {
            exit 1
        }
        return
    }

    # Generate Terraform variables
    $tfvarsFile = New-TerraformVars `
        -Size $Size `
        -Environment $Environment `
        -Location $Location `
        -Owner $Owner `
        -OpenAIKey $OpenAIKey

    if (-not $tfvarsFile) {
        exit 1
    }
    Write-Host ""

    # Plan deployment
    if (-not (Invoke-TerraformPlan -TfvarsFile $tfvarsFile)) {
        Write-ErrorMessage "Terraform plan failed"
        exit 1
    }
    Write-Host ""

    # Apply deployment (unless dry run)
    if ($DryRun) {
        Write-Banner "Dry Run Complete"
        Write-Success "Review the plan above. Run without -DryRun to apply changes."
        Write-Host ""
        Write-Info "To apply manually:"
        Write-Host "  cd $script:TerraformDir" -ForegroundColor Yellow
        Write-Host "  terraform apply tfplan" -ForegroundColor Yellow
    }
    else {
        if (Invoke-TerraformApply -AutoApprove $AutoApprove) {
            Write-Banner "Deployment Complete"
            Write-Success "Infrastructure deployed successfully!"
            Write-Host ""
            Show-NextSteps -Environment $Environment
        }
        else {
            Write-ErrorMessage "Deployment failed"
            exit 1
        }
    }
}

# Run main script
Main
