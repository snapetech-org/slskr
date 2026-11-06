$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url = "https://github.com/snapetech-org/slskr/releases/download/v0.2.82/slskr-v0.2.82-x86_64-pc-windows-msvc.zip"
$checksum = "ab3f4f0a21cc7fe968e2bb22b027ae489bbe29e3ea52051df601cfae934eabf4"

Install-ChocolateyZipPackage -PackageName 'slskr' -Url $url -UnzipLocation $toolsDir -Checksum $checksum -ChecksumType 'sha256'
