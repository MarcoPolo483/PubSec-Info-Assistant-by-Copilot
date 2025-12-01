<#
.SYNOPSIS
    Automated cleanup script for EVA Domain Assistant 2.0 migration

.DESCRIPTION
    This script automates the rebranding from eva-da-2 
    to EVA-DA-2, removing all Copilot/Spark references and updating URLs.

.PARAMETER RepoPath
    Path to the repository root (default: current directory)

.PARAMETER DryRun
    Preview changes without modifying files

.PARAMETER SkipBackup
    Skip creating backup branch (not recommended)

.EXAMPLE
    .\MIGRATION-CLEANUP-SCRIPT.ps1 -DryRun
    Preview all changes without modifying files

.EXAMPLE
    .\MIGRATION-CLEANUP-SCRIPT.ps1
    Execute full cleanup

.NOTES
    Version: 1.0.0
    Author: EVA Suite Team
    Last Updated: 2025-11-30
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$RepoPath = (Get-Location).Path,

    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [switch]$SkipBackup
)

$ErrorActionPreference = "Stop"

# =============================================================================
# Configuration
# =============================================================================

$script:ReplacementPatterns = @(
    # Repository URLs
    @{
        Find    = 'https://github\.com/EVA-Suite/eva-da-2'
        Replace = 'https://github.com/EVA-Suite/eva-da-2'
        Regex   = $true
    },
    @{
        Find    = 'github\.com/EVA-Suite/eva-da-2'
        Replace = 'github.com/EVA-Suite/eva-da-2'
        Regex   = $true
    },
    @{
        Find    = 'EVA-Suite/eva-da-2'
        Replace = 'EVA-Suite/eva-da-2'
        Regex   = $false
    },
    
    # Directory names in paths
    @{
        Find    = 'eva-da-2'
        Replace = 'eva-da-2'
        Regex   = $false
    },
    
    # Branch names
    @{
        Find    = 'main'
        Replace = 'main'
        Regex   = $false
    },
    @{
        Find    = '@main'
        Replace = '@main'
        Regex   = $false
    },
    @{
        Find    = 'origin/main'
        Replace = 'origin/main'
        Regex   = $false
    },
    
    # Container registry paths
    @{
        Find    = 'ghcr\.io/marcopolo483/eva-da-2'
        Replace = 'ghcr.io/eva-suite/eva-da-2'
        Regex   = $true
    },
    @{
        Find    = 'eva-da-2'
        Replace = 'eva-da-2'
        Regex   = $false
    },
    
    # Product names
    @{
        Find    = 'EVA Domain Assistant 2.0'
        Replace = 'EVA Domain Assistant 2.0'
        Regex   = $false
    },
    @{
        Find    = 'EVA Domain Assistant 2.0'
        Replace = 'EVA Domain Assistant 2.0'
        Regex   = $false
    },
    @{
        Find    = 'EVA Domain Assistant 2.0'
        Replace = 'EVA Domain Assistant 2.0'
        Regex   = $false
    },
    
    # Copilot/Spark references (remove completely)
    @{
        Find    = ''
        Replace = ''
        Regex   = $false
    },
    @{
        Find    = ''
        Replace = ''
        Regex   = $false
    },
    @{
        Find    = ''
        Replace = ''
        Regex   = $false
    },
    @{
        Find    = 'EVA Development Team'
        Replace = 'EVA Development Team'
        Regex   = $false
    },
    @{
        Find    = 'Built by EVA Suite Team'
        Replace = 'Built by EVA Suite Team'
        Regex   = $false
    },
    @{
        Find    = ''
        Replace = ''
        Regex   = $false
    }
)

$script:FileExtensions = @(
    '*.md',
    '*.yml',
    '*.yaml',
    '*.tf',
    '*.tfvars',
    '*.json',
    '*.py',
    '*.sh',
    '*.ps1',
    '*.ts',
    '*.tsx',
    '*.js',
    '*.jsx',
    '*.html',
    '*.xml',
    'Dockerfile*',
    'docker-compose.yml'
)

$script:ExcludeDirs = @(
    '.git',
    'node_modules',
    'dist',
    'build',
    '__pycache__',
    '.pytest_cache',
    '.terraform',
    'venv',
    'env'
)

$script:Stats = @{
    FilesScanned  = 0
    FilesModified = 0
    TotalReplacements = 0
    Errors = 0
}

# =============================================================================
# Helper Functions
# =============================================================================

function Write-Banner {
    param([string]$Message)
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
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

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-ErrorMessage {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Test-GitRepository {
    param([string]$Path)
    
    Push-Location $Path
    try {
        git rev-parse --git-dir 2>&1 | Out-Null
        return $LASTEXITCODE -eq 0
    }
    finally {
        Pop-Location
    }
}

function New-BackupBranch {
    Write-Step "Creating backup branch..."
    
    Push-Location $RepoPath
    try {
        $currentBranch = git branch --show-current
        $backupBranch = "pre-eva-da-2-migration"
        
        Write-Info "Current branch: $currentBranch"
        Write-Info "Creating backup: $backupBranch"
        
        git checkout -b $backupBranch 2>&1 | Out-Null
        git push origin $backupBranch 2>&1 | Out-Null
        git checkout $currentBranch 2>&1 | Out-Null
        
        Write-Success "Backup branch created: $backupBranch"
        return $true
    }
    catch {
        Write-ErrorMessage "Failed to create backup branch: $_"
        return $false
    }
    finally {
        Pop-Location
    }
}

function Get-TargetFiles {
    param([string]$RootPath)
    
    Write-Step "Scanning repository for files to process..."
    
    $allFiles = @()
    
    foreach ($ext in $script:FileExtensions) {
        $files = Get-ChildItem -Path $RootPath -Filter $ext -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object {
                $excluded = $false
                foreach ($excludeDir in $script:ExcludeDirs) {
                    if ($_.FullName -like "*\$excludeDir\*") {
                        $excluded = $true
                        break
                    }
                }
                -not $excluded
            }
        
        $allFiles += $files
    }
    
    $uniqueFiles = $allFiles | Select-Object -Unique -ExpandProperty FullName
    
    Write-Success "Found $($uniqueFiles.Count) files to process"
    return $uniqueFiles
}

function Update-FileContent {
    param(
        [string]$FilePath,
        [bool]$IsDryRun
    )
    
    try {
        # Read file content
        $content = Get-Content -Path $FilePath -Raw -ErrorAction Stop
        $originalContent = $content
        $replacementsMade = 0
        
        # Apply all replacement patterns
        foreach ($pattern in $script:ReplacementPatterns) {
            if ($pattern.Regex) {
                $newContent = $content -replace $pattern.Find, $pattern.Replace
            }
            else {
                $newContent = $content.Replace($pattern.Find, $pattern.Replace)
            }
            
            if ($newContent -ne $content) {
                $replacementsMade++
                $content = $newContent
            }
        }
        
        # Only write if changes were made
        if ($content -ne $originalContent) {
            $script:Stats.TotalReplacements += $replacementsMade
            
            if (-not $IsDryRun) {
                Set-Content -Path $FilePath -Value $content -NoNewline
                $script:Stats.FilesModified++
            }
            
            $relativePath = $FilePath.Replace($RepoPath, '').TrimStart('\')
            
            if ($IsDryRun) {
                Write-Info "  [DRY RUN] Would modify: $relativePath ($replacementsMade replacements)"
            }
            else {
                Write-Info "  Modified: $relativePath ($replacementsMade replacements)"
            }
            
            return $true
        }
        
        return $false
    }
    catch {
        Write-Warning "  Failed to process $FilePath`: $_"
        $script:Stats.Errors++
        return $false
    }
}

function Show-Summary {
    Write-Banner "Migration Cleanup Summary"
    
    Write-Host "Files scanned:        $($script:Stats.FilesScanned)" -ForegroundColor Cyan
    Write-Host "Files modified:       $($script:Stats.FilesModified)" -ForegroundColor $(if ($script:Stats.FilesModified -gt 0) { 'Green' } else { 'Gray' })
    Write-Host "Total replacements:   $($script:Stats.TotalReplacements)" -ForegroundColor $(if ($script:Stats.TotalReplacements -gt 0) { 'Green' } else { 'Gray' })
    Write-Host "Errors:               $($script:Stats.Errors)" -ForegroundColor $(if ($script:Stats.Errors -gt 0) { 'Red' } else { 'Gray' })
    
    Write-Host ""
    
    if ($DryRun) {
        Write-Warning "This was a DRY RUN. No files were actually modified."
        Write-Info "Run without -DryRun to apply changes."
    }
    else {
        Write-Success "Cleanup completed successfully!"
        Write-Info "Next steps:"
        Write-Host "  1. Review changes: git diff" -ForegroundColor Yellow
        Write-Host "  2. Test builds and deployments" -ForegroundColor Yellow
        Write-Host "  3. Commit changes: git add . && git commit" -ForegroundColor Yellow
        Write-Host "  4. Push to repository: git push" -ForegroundColor Yellow
    }
}

function Show-ReplacementPatterns {
    Write-Banner "Replacement Patterns"
    
    Write-Info "The following patterns will be replaced:"
    Write-Host ""
    
    foreach ($pattern in $script:ReplacementPatterns) {
        Write-Host "  Find:    " -NoNewline -ForegroundColor Gray
        Write-Host $pattern.Find -ForegroundColor Yellow
        Write-Host "  Replace: " -NoNewline -ForegroundColor Gray
        Write-Host $(if ($pattern.Replace) { $pattern.Replace } else { "(remove)" }) -ForegroundColor Green
        Write-Host ""
    }
}

# =============================================================================
# Main Execution
# =============================================================================

function Main {
    Write-Banner "EVA Domain Assistant 2.0 - Migration Cleanup Script"
    
    # Validate repository
    Write-Step "Validating repository..."
    if (-not (Test-Path $RepoPath)) {
        Write-ErrorMessage "Repository path not found: $RepoPath"
        exit 1
    }
    
    if (-not (Test-GitRepository -Path $RepoPath)) {
        Write-ErrorMessage "Not a Git repository: $RepoPath"
        exit 1
    }
    
    Write-Success "Repository validated: $RepoPath"
    Write-Host ""
    
    # Show what will be replaced
    Show-ReplacementPatterns
    
    # Create backup branch
    if (-not $SkipBackup -and -not $DryRun) {
        if (-not (New-BackupBranch)) {
            Write-Warning "Backup branch creation failed. Continue anyway? (Y/N)"
            $response = Read-Host
            if ($response -ne 'Y') {
                Write-Info "Operation cancelled."
                exit 0
            }
        }
        Write-Host ""
    }
    
    # Get target files
    $targetFiles = Get-TargetFiles -RootPath $RepoPath
    $script:Stats.FilesScanned = $targetFiles.Count
    Write-Host ""
    
    # Confirm before proceeding
    if (-not $DryRun) {
        Write-Warning "This will modify $($targetFiles.Count) files. Continue? (Y/N)"
        $response = Read-Host
        if ($response -ne 'Y') {
            Write-Info "Operation cancelled."
            exit 0
        }
        Write-Host ""
    }
    
    # Process files
    Write-Step "Processing files..."
    Write-Host ""
    
    $progress = 0
    foreach ($file in $targetFiles) {
        $progress++
        
        if ($progress % 10 -eq 0) {
            Write-Progress -Activity "Processing files" -Status "$progress of $($targetFiles.Count)" -PercentComplete (($progress / $targetFiles.Count) * 100)
        }
        
        Update-FileContent -FilePath $file -IsDryRun $DryRun | Out-Null
    }
    
    Write-Progress -Activity "Processing files" -Completed
    Write-Host ""
    
    # Show summary
    Show-Summary
}

# Run main script
Main
