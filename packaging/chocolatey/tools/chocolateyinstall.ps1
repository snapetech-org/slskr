$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url = "https://github.com/snapetech-org/slskr/releases/download/v0.2.86/slskr-v0.2.86-x86_64-pc-windows-msvc.zip"
$checksum = "aa1e6d7ccf5a8ef161bf91d7c0dee7105774ec7f576bff9e69336116cd96cad8"

Install-ChocolateyZipPackage -PackageName 'slskr' -Url $url -UnzipLocation $toolsDir -Checksum $checksum -ChecksumType 'sha256'
