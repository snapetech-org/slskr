$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url = "https://github.com/snapetech-org/slskr/releases/download/release-v0.2.74/slskr-v0.2.74-x86_64-pc-windows-msvc.zip"
$checksum = "080c9fb207ac31f01501054b89e4dc9d4e82b3e2ce818589835024f8e1c15da2"

Install-ChocolateyZipPackage -PackageName 'slskr' -Url $url -UnzipLocation $toolsDir -Checksum $checksum -ChecksumType 'sha256'
