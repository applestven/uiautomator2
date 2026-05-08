# 离线依赖下载脚本（Windows PowerShell）
# 作用：把 requirements.txt 中的依赖下载为 .whl/.tar.gz，便于拷贝到别的项目离线安装
# 用法：在本仓库根目录执行：powershell -ExecutionPolicy Bypass -File .\temp\soul\download_wheels.ps1

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$req = Join-Path $PSScriptRoot 'requirements.txt'
$wheelhouse = Join-Path $PSScriptRoot 'wheelhouse'

if (!(Test-Path $req)) {
  throw "requirements.txt not found: $req"
}

New-Item -ItemType Directory -Force -Path $wheelhouse | Out-Null

$python = Join-Path $root '.venv\Scripts\python.exe'
if (!(Test-Path $python)) {
  throw "python venv not found: $python  (请先在仓库根目录创建并启用 .venv)"
}

# 建议先升级 pip，确保能下载到合适的 wheel
& $python -m pip install -U pip

# 下载依赖（包含依赖的依赖）
& $python -m pip download -r $req -d $wheelhouse

Write-Host "OK. Wheels downloaded to: $wheelhouse"
