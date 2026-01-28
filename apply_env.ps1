# apply_env.ps1
# This script copies the master.env to the .env files of all sub-projects.

$SourceFile = "master.env"
$Destinations = @(
    "water_dp-api\.env",
    "water_dp-geo\.env",
    "water_dp-hydro_portal\.env",
    "timeio\tsm-orchestration\.env"
)

if (-Not (Test-Path $SourceFile)) {
    Write-Error "Could not find $SourceFile in the current directory."
    exit 1
}

foreach ($Dest in $Destinations) {
    $DestPath = Join-Path (Get-Location) $Dest
    $DestDir = Split-Path $DestPath
    
    if (Test-Path $DestDir) {
        Write-Host "Applying configuration to $Dest..."
        Copy-Item -Path $SourceFile -Destination $DestPath -Force
    } else {
        Write-Warning "Directory $DestDir does not exist, skipping."
    }
}

Write-Host "`nEnvironment configuration applied successfully!" -ForegroundColor Green
