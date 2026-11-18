# 把 .env 载入当前 PowerShell 会话：  .\env.ps1
Get-Content (Join-Path $PSScriptRoot '.env') | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith('#')) { return }
    $i = $line.IndexOf('=')
    if ($i -lt 1) { return }
    $name = $line.Substring(0, $i).Trim()
    $value = $line.Substring($i + 1).Trim().Trim('"').Trim("'")
    Set-Item -Path "Env:$name" -Value $value
}
Write-Host "env loaded: $env:ANTHROPIC_MODEL @ $env:ANTHROPIC_BASE_URL"
