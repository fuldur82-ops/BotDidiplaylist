param(
    [string]$OutputZip = "BotDidi-discloud.zip"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$stage = Join-Path $projectRoot "discloud-package"
$outputPath = Join-Path $projectRoot $OutputZip

if (-not (Test-Path (Join-Path $projectRoot ".env"))) {
    throw "Missing .env file. Create .env with DISCORD_TOKEN before building."
}

if (Test-Path $stage) {
    Remove-Item -LiteralPath $stage -Recurse -Force
}

New-Item -ItemType Directory -Path $stage | Out-Null
New-Item -ItemType Directory -Path (Join-Path $stage "cogs") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $stage "utils") | Out-Null

Copy-Item -LiteralPath (Join-Path $projectRoot "cogs\music.py"), (Join-Path $projectRoot "cogs\__init__.py") -Destination (Join-Path $stage "cogs")
Copy-Item -LiteralPath (Join-Path $projectRoot "utils\amazon.py"), (Join-Path $projectRoot "utils\spotify.py"), (Join-Path $projectRoot "utils\validators.py"), (Join-Path $projectRoot "utils\youtube.py"), (Join-Path $projectRoot "utils\__init__.py") -Destination (Join-Path $stage "utils")
Copy-Item -LiteralPath (Join-Path $projectRoot "main.py"), (Join-Path $projectRoot "requirements.txt"), (Join-Path $projectRoot "discloud.config"), (Join-Path $projectRoot "README.md"), (Join-Path $projectRoot ".env.example"), (Join-Path $projectRoot ".env") -Destination $stage

if (Test-Path $outputPath) {
    Remove-Item -LiteralPath $outputPath -Force
}

Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $outputPath

Write-Output "Built: $outputPath"
