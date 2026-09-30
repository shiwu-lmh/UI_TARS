$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $MyInvocation.MyCommand.Path
$shim = Join-Path $repo 'node-userinfo-shim.cjs'
$screenshotDir = Join-Path (Split-Path -Parent $repo) 'screenshots'
$userDataDir = Join-Path $repo '.ui-tars-user-data'

Push-Location $repo
try {
  $env:NODE_OPTIONS = "--require=$shim"
  $env:UI_TARS_SCREENSHOT_DIR = $screenshotDir
  $env:UI_TARS_USER_DATA_DIR = $userDataDir
  $env:UI_TARS_REQUEST_TIMEOUT_MS = '120000'
  pnpm dev:ui-tars
}
finally {
  Pop-Location
}
