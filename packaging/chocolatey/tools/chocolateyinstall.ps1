$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url = "https://github.com/snapetech-org/slskr/releases/download/v0.2.83/slskr-v0.2.83-x86_64-pc-windows-msvc.zip"
$checksum = "68506de84bcd35e98f49d797eb65d49eeaa5b7aa5a90a6e6a7cf134417385f21"

Install-ChocolateyZipPackage -PackageName 'slskr' -Url $url -UnzipLocation $toolsDir -Checksum $checksum -ChecksumType 'sha256'
