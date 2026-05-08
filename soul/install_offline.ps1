# 离线安装脚本（拷贝到目标项目后使用）
# 前提：同目录下存在 requirements.txt 与 wheelhouse/（由 download_wheels.ps1 生成）
# 用法：powershell -ExecutionPolicy Bypass -File .\install_offline.ps1

$ErrorActionPreference = 'Stop'

$req = Join-Path $PSScriptRoot 'requirements.txt'
$wheelhouse = Join-Path $PSScriptRoot 'wheelhouse'

if (!(Test-Path $req)) { throw "requirements.txt not found: $req" }
if (!(Test-Path $wheelhouse)) { throw "wheelhouse not found: $wheelhouse" }

python -m pip install --no-index --find-links $wheelhouse -r $req

Write-Host "OK. Offline install done."
