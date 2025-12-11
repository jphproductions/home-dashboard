#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Migrates home-dashboard from nested structure to flat structure.

.DESCRIPTION
    This script flattens the nested home_dashboard/home_dashboard/ structure to
    a single home_dashboard/ directory at the project root. It:
    
    1. Moves home_dashboard/home_dashboard/* -> home_dashboard/
    2. Moves home_dashboard/pyproject.toml -> pyproject.toml (root)
    3. Moves home_dashboard/poetry.lock -> poetry.lock (root)
    4. Updates all Python imports from home_dashboard.home_dashboard.X to home_dashboard.X
    5. Updates Docker configuration files
    6. Updates VS Code tasks
    7. Updates systemd service files (if needed)
    
    Uses git mv for history preservation.

.PARAMETER PreviewOnly
    Show what would be done without actually doing it.

.EXAMPLE
    .\Migrate-ProjectStructure.ps1 -PreviewOnly
    Shows all planned operations without executing them.

.EXAMPLE
    .\Migrate-ProjectStructure.ps1
    Executes the migration.
#>

param(
    [switch]$PreviewOnly
)

$ErrorActionPreference = "Stop"

# Project root directory
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "🚀 Home Dashboard Project Structure Migration" -ForegroundColor Cyan
Write-Host "=" * 60

if ($PreviewOnly) {
    Write-Host "⚠️  Preview mode: No changes will be made" -ForegroundColor Yellow
    Write-Host ""
}

# Verify we're in the right directory
if (-not (Test-Path "home_dashboard\home_dashboard\main.py")) {
    Write-Error "❌ Not in correct directory. Expected to find home_dashboard\home_dashboard\main.py"
    exit 1
}

Write-Host "✅ Current directory verified: $ProjectRoot" -ForegroundColor Green
Write-Host ""

#region Step 1: Create temporary directory for safe migration
Write-Host "📦 Step 1: Creating temporary directory..." -ForegroundColor Cyan

$TempDir = Join-Path $ProjectRoot "temp_migration"

if (-not $PreviewOnly) {
    if (Test-Path $TempDir) {
        Remove-Item $TempDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $TempDir | Out-Null
    Write-Host "   Created: $TempDir" -ForegroundColor Green
} else {
    Write-Host "   Would create: $TempDir" -ForegroundColor Yellow
}

#endregion

#region Step 2: Move Python package contents using git mv
Write-Host ""
Write-Host "📦 Step 2: Moving Python package contents with git mv..." -ForegroundColor Cyan

$SourcePackage = "home_dashboard\home_dashboard"
$TargetTemp = Join-Path $TempDir "home_dashboard"

# Get all items in the nested package
$ItemsToMove = Get-ChildItem -Path $SourcePackage -Force | Where-Object { $_.Name -ne ".pytest_cache" }

Write-Host "   Found $($ItemsToMove.Count) items to move:" -ForegroundColor White

foreach ($Item in $ItemsToMove) {
    $RelativePath = $Item.Name
    $SourcePath = $Item.FullName
    $DestPath = Join-Path $TempDir "home_dashboard" | Join-Path -ChildPath $RelativePath
    
    if (-not $PreviewOnly) {
        # Ensure parent directory exists
        $DestParent = Split-Path -Parent $DestPath
        if (-not (Test-Path $DestParent)) {
            New-Item -ItemType Directory -Path $DestParent -Force | Out-Null
        }
        
        # Use git mv for history preservation
        Write-Host "   git mv $SourcePath -> $DestPath" -ForegroundColor Gray
        git mv $SourcePath $DestPath
    } else {
        Write-Host "   Would: git mv $SourcePath -> $DestPath" -ForegroundColor Yellow
    }
}

#endregion

#region Step 3: Move pyproject.toml and poetry.lock
Write-Host ""
Write-Host "📦 Step 3: Moving pyproject.toml and poetry.lock..." -ForegroundColor Cyan

$FilesToMove = @(
    @{ Source = "home_dashboard\pyproject.toml"; Dest = "pyproject.toml" },
    @{ Source = "home_dashboard\poetry.lock"; Dest = "poetry.lock" }
)

foreach ($File in $FilesToMove) {
    $SourcePath = Join-Path $ProjectRoot $File.Source
    $DestPath = Join-Path $ProjectRoot $File.Dest
    
    if (Test-Path $SourcePath) {
        if (-not $PreviewOnly) {
            Write-Host "   git mv $($File.Source) -> $($File.Dest)" -ForegroundColor Gray
            git mv $SourcePath $DestPath
        } else {
            Write-Host "   Would: git mv $($File.Source) -> $($File.Dest)" -ForegroundColor Yellow
        }
    }
}

#endregion

#region Step 4: Clean up old nested directory
Write-Host ""
Write-Host "🗑️  Step 4: Removing old nested directory..." -ForegroundColor Cyan

if (-not $PreviewOnly) {
    # Remove the now-empty home_dashboard/home_dashboard directory
    if (Test-Path "home_dashboard\home_dashboard") {
        Remove-Item "home_dashboard\home_dashboard" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "   Removed: home_dashboard\home_dashboard" -ForegroundColor Green
    }
    
    # Remove the old home_dashboard directory if it's empty
    $RemainingItems = Get-ChildItem "home_dashboard" -Force | Where-Object { $_.Name -ne ".pytest_cache" }
    if ($RemainingItems.Count -eq 0) {
        Remove-Item "home_dashboard" -Recurse -Force
        Write-Host "   Removed: home_dashboard (was empty)" -ForegroundColor Green
    }
} else {
    Write-Host "   Would remove: home_dashboard\home_dashboard" -ForegroundColor Yellow
    Write-Host "   Would remove: home_dashboard (if empty)" -ForegroundColor Yellow
}

#endregion

#region Step 5: Move temp directory to final location
Write-Host ""
Write-Host "📦 Step 5: Moving from temp to final location..." -ForegroundColor Cyan

if (-not $PreviewOnly) {
    Move-Item (Join-Path $TempDir "home_dashboard") "home_dashboard" -Force
    Remove-Item $TempDir -Recurse -Force
    Write-Host "   Moved temp_migration\home_dashboard -> home_dashboard" -ForegroundColor Green
} else {
    Write-Host "   Would move: temp_migration\home_dashboard -> home_dashboard" -ForegroundColor Yellow
}

#endregion

#region Step 6: Update Python imports
Write-Host ""
Write-Host "🔧 Step 6: Updating Python imports..." -ForegroundColor Cyan

$PythonFiles = Get-ChildItem -Path "home_dashboard", "tests" -Include "*.py" -Recurse -File

Write-Host "   Found $($PythonFiles.Count) Python files to update" -ForegroundColor White

$ImportPattern = 'from home_dashboard\.home_dashboard\.'
$ReplacementPattern = 'from home_dashboard.'

$UpdatedCount = 0

foreach ($File in $PythonFiles) {
    $Content = Get-Content $File.FullName -Raw
    
    if ($Content -match $ImportPattern) {
        if (-not $PreviewOnly) {
            $UpdatedContent = $Content -replace $ImportPattern, $ReplacementPattern
            Set-Content $File.FullName -Value $UpdatedContent -NoNewline
            $UpdatedCount++
            Write-Host "   Updated: $($File.FullName)" -ForegroundColor Gray
        } else {
            $UpdatedCount++
            Write-Host "   Would update: $($File.FullName)" -ForegroundColor Yellow
        }
    }
}

# Also check for import home_dashboard.home_dashboard pattern
$ImportPattern2 = 'import home_dashboard\.home_dashboard'
$ReplacementPattern2 = 'import home_dashboard'

foreach ($File in $PythonFiles) {
    $Content = Get-Content $File.FullName -Raw
    
    if ($Content -match $ImportPattern2) {
        if (-not $PreviewOnly) {
            $UpdatedContent = $Content -replace $ImportPattern2, $ReplacementPattern2
            Set-Content $File.FullName -Value $UpdatedContent -NoNewline
            Write-Host "   Updated: $($File.FullName)" -ForegroundColor Gray
        } else {
            Write-Host "   Would update: $($File.FullName)" -ForegroundColor Yellow
        }
    }
}

Write-Host "   Updated $UpdatedCount files" -ForegroundColor Green

#endregion

#region Step 7: Update pyproject.toml
Write-Host ""
Write-Host "🔧 Step 7: Updating pyproject.toml..." -ForegroundColor Cyan

$PyprojectPath = Join-Path $ProjectRoot "pyproject.toml"

if (Test-Path $PyprojectPath) {
    $Content = Get-Content $PyprojectPath -Raw
    
    # Update testpaths
    $Content = $Content -replace 'testpaths = \["\.\./tests"\]', 'testpaths = ["tests"]'
    
    if (-not $PreviewOnly) {
        Set-Content $PyprojectPath -Value $Content -NoNewline
        Write-Host "   Updated testpaths in pyproject.toml" -ForegroundColor Green
    } else {
        Write-Host "   Would update testpaths in pyproject.toml" -ForegroundColor Yellow
    }
}

#endregion

#region Step 8: Update Docker files
Write-Host ""
Write-Host "🔧 Step 8: Updating Docker configuration..." -ForegroundColor Cyan

# Update Dockerfile
$DockerfilePath = "docker\Dockerfile.api"
if (Test-Path $DockerfilePath) {
    $Content = Get-Content $DockerfilePath -Raw
    
    # Update COPY commands
    $Content = $Content -replace 'COPY home_dashboard /app/home_dashboard', 'COPY home_dashboard /code/home_dashboard'
    $Content = $Content -replace 'WORKDIR /app/home_dashboard', 'WORKDIR /code'
    $Content = $Content -replace '/app/', '/code/'
    
    if (-not $PreviewOnly) {
        Set-Content $DockerfilePath -Value $Content -NoNewline
        Write-Host "   Updated: docker\Dockerfile.api" -ForegroundColor Green
    } else {
        Write-Host "   Would update: docker\Dockerfile.api" -ForegroundColor Yellow
    }
}

# Update docker-compose.yml
$DockerComposePath = "docker\docker-compose.yml"
if (Test-Path $DockerComposePath) {
    $Content = Get-Content $DockerComposePath -Raw
    
    # No changes needed for compose - it references Dockerfile
    Write-Host "   docker-compose.yml: No changes needed" -ForegroundColor Gray
}

#endregion

#region Step 9: Update VS Code tasks
Write-Host ""
Write-Host "🔧 Step 9: Updating VS Code tasks.json..." -ForegroundColor Cyan

$TasksPath = ".vscode\tasks.json"
if (Test-Path $TasksPath) {
    $Content = Get-Content $TasksPath -Raw
    
    # Update cd commands
    $Content = $Content -replace 'cd home_dashboard && poetry', 'poetry'
    $Content = $Content -replace 'cd home_dashboard;', ''
    
    if (-not $PreviewOnly) {
        Set-Content $TasksPath -Value $Content -NoNewline
        Write-Host "   Updated: .vscode\tasks.json" -ForegroundColor Green
    } else {
        Write-Host "   Would update: .vscode\tasks.json" -ForegroundColor Yellow
    }
}

#endregion

#region Step 10: Verify migration
Write-Host ""
Write-Host "🔍 Step 10: Verifying migration..." -ForegroundColor Cyan

if (-not $PreviewOnly) {
    # Check if new structure exists
    $RequiredPaths = @(
        "home_dashboard\main.py",
        "home_dashboard\config.py",
        "home_dashboard\routers",
        "home_dashboard\services",
        "pyproject.toml",
        "poetry.lock"
    )
    
    $AllExist = $true
    foreach ($Path in $RequiredPaths) {
        if (Test-Path $Path) {
            Write-Host "   ✅ Found: $Path" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Missing: $Path" -ForegroundColor Red
            $AllExist = $false
        }
    }
    
    if ($AllExist) {
        Write-Host ""
        Write-Host "✅ Migration completed successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 Next steps:" -ForegroundColor Cyan
        Write-Host "   1. Run: poetry install" -ForegroundColor White
        Write-Host "   2. Run: poetry run python -c 'import home_dashboard'" -ForegroundColor White
        Write-Host "   3. Run: poetry run pytest --collect-only" -ForegroundColor White
        Write-Host "   4. Run: poetry run uvicorn home_dashboard.main:app" -ForegroundColor White
        Write-Host "   5. If all works, commit changes with git" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "⚠️  Migration completed but some files are missing!" -ForegroundColor Yellow
    }
} else {
    Write-Host "   WhatIf mode - skipping verification" -ForegroundColor Yellow
}

#endregion

Write-Host ""
Write-Host "=" * 60
Write-Host "✨ Migration script complete!" -ForegroundColor Cyan
