param([Parameter(Mandatory=$true)][string]$Archive)
$ErrorActionPreference = 'Stop'
# Custom scans with DisableRemediation ignore hosted-image exclusions and scan archives.
# https://learn.microsoft.com/en-us/defender-endpoint/command-line-arguments-microsoft-defender-antivirus
Update-MpSignature
Get-MpComputerStatus | Select-Object AMProductVersion, AMEngineVersion, AntivirusSignatureVersion, AntivirusSignatureLastUpdated | Format-List
$platform = Get-ChildItem "$env:ProgramData/Microsoft/Windows Defender/Platform" -Directory | Sort-Object Name -Descending | Select-Object -First 1
$scanner = if ($platform) { Join-Path $platform.FullName 'MpCmdRun.exe' } else { "$env:ProgramFiles/Windows Defender/MpCmdRun.exe" }
$archivePath = (Resolve-Path $Archive).Path
$unpacked = Join-Path $env:RUNNER_TEMP 'defender-release-scan'
Expand-Archive -Path $archivePath -DestinationPath $unpacked -Force
foreach ($target in @($archivePath, $unpacked)) {
    & $scanner -Scan -ScanType 3 -File $target -DisableRemediation
    if ($LASTEXITCODE -ne 0) { throw "Defender release scan failed for $target (exit $LASTEXITCODE)" }
}
Write-Host 'Microsoft Defender scanned the archive and extracted release without detections.'
