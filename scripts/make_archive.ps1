# Скрипт сборки архива проекта для сдачи/презентации
# Использование: pwsh -File .\scripts\make_archive.ps1

param(
    [string]$OutFile = "Ecobg_Project.zip"
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$dest = Join-Path $root $OutFile

# Исключения (папки и файлы, которые не нужны в архиве)
$exclude = @(
    ".git", "**/.git/**",
    "**/__pycache__/**",
    ".venv", "venv", "env", "**/.venv/**", "**/venv/**", "**/env/**",
    "**/*.pyc",
    "**/.mypy_cache/**",
    "**/.pytest_cache/**",
    "**/.DS_Store",
    "**/.idea/**",
    "**/.vscode/**",
    "**/*.log"
)

if (Test-Path $dest) { Remove-Item $dest -Force }

# Собираем список файлов с исключениями
$items = Get-ChildItem -Path $root -Recurse -File | Where-Object {
    $path = $_.FullName.Substring($root.Length + 1)
    foreach ($ex in $exclude) {
        if ([System.Management.Automation.WildcardPattern]::new($ex, 'IgnoreCase').IsMatch($path)) { return $false }
    }
    return $true
}

# Создаём временную папку и копируем отфильтрованные файлы
$tmp = New-Item -ItemType Directory -Path (Join-Path $env:TEMP "ecobg_zip_$(Get-Random)")
foreach ($f in $items) {
    $rel = $f.FullName.Substring($root.Length + 1)
    $target = Join-Path $tmp $rel
    New-Item -ItemType Directory -Force -Path (Split-Path $target -Parent) | Out-Null
    Copy-Item $f.FullName -Destination $target -Force
}

Compress-Archive -Path (Join-Path $tmp '*') -DestinationPath $dest -Force
Remove-Item $tmp -Recurse -Force
Write-Host "[OK] Архив собран: $dest"
