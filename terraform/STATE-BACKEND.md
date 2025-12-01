# Terraform Remote State Backend

This project uses an Azure Storage Account backend for Terraform state.

## Backend settings (defaults in `main.tf`)
- `resource_group_name`: `pubsec-terraform-state-rg`
- `storage_account_name`: `pubsecterraformstate` (must be globally unique)
- `container_name`: `tfstate`
- `key`: `pubsec-info-assistant.tfstate`

## Bootstrapping state resources
Use the provided script to create the Resource Group, Storage Account, and blob container:

```pwsh
pwsh -File .\terraform\scripts\bootstrap-remote-state.ps1 `
  -SubscriptionId "<SUBSCRIPTION_ID>" `
  -Location "eastus" `
  -ResourceGroupName "pubsec-terraform-state-rg" `
  -StorageAccountName "pubsecterraformstate" `
  -ContainerName "tfstate" `
  -AutoSuffixIfTaken
```

If the storage account name is taken, the script (with `-AutoSuffixIfTaken`) will append a random suffix and print the final name.

## Initializing with backend overrides
You can (and often should) use backend overrides instead of editing `main.tf`:

```pwsh
Push-Location .\terraform
terraform init -reconfigure `
  -backend-config=resource_group_name=pubsec-terraform-state-rg `
  -backend-config=storage_account_name=<FINAL_SA_NAME> `
  -backend-config=container_name=tfstate `
  -backend-config=key=pubsec-info-assistant.tfstate
Pop-Location
```

> Note: Terraform backend blocks do not support variables. Use `-backend-config` for per-environment customization.
