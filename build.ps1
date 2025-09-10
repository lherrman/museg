#!/usr/bin/env pwsh
# Build script for MuSeg Audio Annotation Tool Windows executable

param(
    [switch]$Clean,
    [switch]$Debug
)

# Colors for output
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }

Write-Info "========================================="
Write-Info "  MuSeg Audio Annotation Tool Build Script"
Write-Info "========================================="

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Error "Virtual environment not found. Please run 'uv venv' first."
    exit 1
}

# Activate virtual environment
Write-Info "Activating virtual environment..."
& ".\.venv\Scripts\Activate.ps1"

# Clean previous builds if requested
if ($Clean) {
    Write-Info "Cleaning previous builds..."
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "*.spec") { Remove-Item -Force "*.spec" }
}

# Install PyInstaller if not present
Write-Info "Installing/updating PyInstaller..."
& python -m pip install pyinstaller

# Create build directory
New-Item -ItemType Directory -Force -Path "build" | Out-Null

# Prepare icon for executable
$IconPath = "build\app_icon.ico"
$SourceIconPath = "src\assets\icon.ico"

if (Test-Path $SourceIconPath) {
    Write-Info "Using existing ICO icon from assets..."
    Copy-Item $SourceIconPath $IconPath
} else {
    Write-Warning "ICO icon not found at $SourceIconPath"
    # Fallback to PNG conversion if ICO not available
    $PngIconPath = "src\assets\icon.png"
    if (Test-Path $PngIconPath) {
        Write-Info "Converting PNG icon to ICO format..."
        $IconScript = @"
try:
    from PIL import Image
    import sys
    img = Image.open('$($PngIconPath -replace '\\', '/')')
    # ICO format supports multiple sizes - create a multi-size ICO
    img.save('$($IconPath -replace '\\', '/')', format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
    print('Icon converted successfully')
except ImportError:
    print('Installing Pillow for icon conversion...')
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pillow'])
    from PIL import Image
    img = Image.open('$($PngIconPath -replace '\\', '/')')
    img.save('$($IconPath -replace '\\', '/')', format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
    print('Icon converted successfully')
except Exception as e:
    print(f'Icon conversion failed: {e}')
    exit(1)
"@
        & python -c $IconScript
    } else {
        Write-Warning "No icon files found"
    }
}

# PyInstaller arguments
$PyInstallerArgs = @(
    "run_labeler.py"
    "--name=museg_win_64"
    "--onefile"
    "--windowed"
    "--distpath=dist"
    "--workpath=build"
    "--specpath=build"
    "--paths=src"
)

# Add icon if it exists
if (Test-Path $IconPath) {
    $AbsoluteIconPath = (Resolve-Path $IconPath).Path
    $PyInstallerArgs += "--icon=$AbsoluteIconPath"
}

# Add debug console if requested
if ($Debug) {
    Write-Info "Building with debug console enabled..."
    $PyInstallerArgs = $PyInstallerArgs | Where-Object { $_ -ne "--windowed" }
    $PyInstallerArgs += "--console"
} else {
    Write-Info "Building windowed application (no console)..."
}

# Hidden imports for dependencies that might not be auto-detected
$PyInstallerArgs += @(
    "--hidden-import=librosa"
    "--hidden-import=soundfile"
    "--hidden-import=matplotlib"
    "--hidden-import=numpy"
    "--hidden-import=PySide6.QtCore"
    "--hidden-import=PySide6.QtWidgets" 
    "--hidden-import=PySide6.QtGui"
    "--hidden-import=PySide6.QtMultimedia"
    "--hidden-import=PySide6.QtMultimediaWidgets"
)

# Additional data files and folders to include
$PyInstallerArgs += @(
    "--add-data=$(Resolve-Path 'src\assets\icon.png');assets"
)

Write-Info "Building executable with PyInstaller..."
Write-Info "Command: pyinstaller $($PyInstallerArgs -join ' ')"

& python -m PyInstaller @PyInstallerArgs

if ($LASTEXITCODE -eq 0) {
    Write-Success "`nBuild completed successfully!"
    Write-Info "Executable location: $(Resolve-Path 'dist\museg_win_64.exe')"
    
    # Get file size
    $ExeFile = Get-Item "dist\museg_win_64.exe"
    $FileSizeMB = [math]::Round($ExeFile.Length / 1MB, 2)
    Write-Info "Executable size: $FileSizeMB MB"
    
    Write-Info "`nTo test the executable:"
    Write-Info "  cd dist"
    Write-Info "  .\museg_win_64.exe"
    
    Write-Info "`nTo create a distribution package:"
    Write-Info "  Create a folder with:"
    Write-Info "  - museg_win_64.exe"
    Write-Info "  - README.md (optional)"
    Write-Info "  - Sample project folder (optional)"
    
} else {
    Write-Error "`nBuild failed! Check the output above for errors."
    exit 1
}
