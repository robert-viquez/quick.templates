$ErrorActionPreference = "Stop"

$appName = "QuickTemplates"
$installDir = "$env:LOCALAPPDATA\Programs\$appName"
$exePath = "$installDir\$appName.exe"

$url = "https://github.com/robert-viquez/quick.templates/releases/latest/download/QuickTemplates.exe"

Write-Host "Installing QuickTemplates..."

# Crear carpeta
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

# Descargar última versión
Invoke-WebRequest -Uri $url -OutFile $exePath

# Crear acceso directo en Start Menu
$startMenu = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
$shortcutPath = "$startMenu\QuickTemplates.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = $installDir
$shortcut.Save()

Write-Host ""
Write-Host "QuickTemplates installed successfully."
Write-Host "Location: $exePath"

# Abrir aplicación
Start-Process $exePath