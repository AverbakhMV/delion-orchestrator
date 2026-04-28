$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$releaseRoot = Join-Path $repoRoot "releases\beta"
$target = Join-Path $releaseRoot "delion"
$archive = Join-Path $releaseRoot "delion-gigacode.zip"

if (-not ((Resolve-Path $releaseRoot).Path).StartsWith($repoRoot)) {
    throw "Release directory is outside repository: $releaseRoot"
}

if (Test-Path -LiteralPath $target) {
    Remove-Item -LiteralPath $target -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $target | Out-Null

Copy-Item -LiteralPath (Join-Path $repoRoot "gigacode-extension.json") -Destination $target -Force
Copy-Item -LiteralPath (Join-Path $repoRoot "GIGACODE.md") -Destination $target -Force
Copy-Item -LiteralPath (Join-Path $repoRoot "main.py") -Destination $target -Force

$commandsTarget = Join-Path $target "commands"
$orchestratorTarget = Join-Path $target "orchestrator"
New-Item -ItemType Directory -Force -Path $commandsTarget | Out-Null
New-Item -ItemType Directory -Force -Path $orchestratorTarget | Out-Null
Copy-Item -Path (Join-Path $repoRoot "commands\*") -Destination $commandsTarget -Recurse -Force

$runtimeModules = @(
    "__init__.py",
    "artifacts.py",
    "cli.py",
    "models.py",
    "validation.py"
)

foreach ($module in $runtimeModules) {
    Copy-Item -LiteralPath (Join-Path $repoRoot "orchestrator\$module") -Destination $orchestratorTarget -Force
}

Get-ChildItem -LiteralPath $target -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -LiteralPath $target -Recurse -File |
    Where-Object { $_.Extension -in @(".pyc", ".pyo") } |
    Remove-Item -Force

if (-not (Test-Path -LiteralPath (Join-Path $target "main.py"))) {
    throw "Release snapshot is incomplete: main.py was not copied"
}

if (Test-Path -LiteralPath $archive) {
    Remove-Item -LiteralPath $archive -Force
}

Compress-Archive -LiteralPath $target -DestinationPath $archive -Force
Write-Host "Built $archive"
