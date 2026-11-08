$ErrorActionPreference = 'Stop'
$root = Join-Path ([IO.Path]::GetTempPath()) ('slskr-winget-test-' + [Guid]::NewGuid())
$null = New-Item -ItemType Directory -Path $root
$originalToken = $env:WINGETCREATE_GITHUB_TOKEN
$originalSummary = $env:GITHUB_STEP_SUMMARY
try {
    $env:WINGETCREATE_GITHUB_TOKEN = 'test-token-only'
    $env:GITHUB_STEP_SUMMARY = ''
    foreach ($name in @('snapetech.slskr.yaml', 'snapetech.slskr.installer.yaml', 'snapetech.slskr.locale.en-US.yaml')) {
        [IO.File]::WriteAllText((Join-Path $root $name), "PackageIdentifier: snapetech.slskr`nPackageVersion: 9.8.7`n")
    }
    $global:SlskrWingetTestRoot = $root
    function Invoke-RestMethod {
        param($Method, $Uri, $Headers, $ErrorAction, $Body, $ContentType)
        $global:SlskrWingetTestRequests.Add(@{ Method = $Method; Uri = $Uri; Body = $Body })
        switch -Regex ($Uri) {
            '^https://api.github.com/user$' { return [pscustomobject]@{ login = 'release-user' } }
            '^https://api.github.com/repos/microsoft/winget-pkgs$' { return [pscustomobject]@{ default_branch = 'master' } }
            '^https://api.github.com/repos/microsoft/winget-pkgs/git/ref/heads/master$' {
                return [pscustomobject]@{ object = [pscustomobject]@{ sha = ('1' * 40) } }
            }
            '^https://api.github.com/repos/release-user/winget-pkgs$' {
                return [pscustomobject]@{ owner = [pscustomobject]@{ login = 'snapetech-org' }; name = 'winget-pkgs'; default_branch = 'master' }
            }
            '^https://api.github.com/repos/snapetech-org/winget-pkgs/git/ref/heads/slskr-release-9.8.7$' {
                if ($global:SlskrWingetTestCase -in @('existing', 'mismatch')) {
                    return [pscustomobject]@{ object = [pscustomobject]@{ sha = ('4' * 40) } }
                }
                throw [Microsoft.PowerShell.Commands.HttpResponseException]::new('Missing ref', [Net.Http.HttpResponseMessage]::new([Net.HttpStatusCode]::NotFound))
            }
            '^https://api.github.com/repos/snapetech-org/winget-pkgs/contents/manifests/' {
                $name = ($Uri.Split('/')[-1]).Split('?')[0]
                $text = [IO.File]::ReadAllText((Join-Path $global:SlskrWingetTestRoot $name))
                if ($global:SlskrWingetTestCase -eq 'mismatch') { $text += 'changed' }
                return [pscustomobject]@{ content = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($text)) }
            }
            '^https://api.github.com/repos/microsoft/winget-pkgs/git/commits/' {
                return [pscustomobject]@{ tree = [pscustomobject]@{ sha = ('2' * 40) } }
            }
            '^https://api.github.com/repos/snapetech-org/winget-pkgs/git/trees$' { return [pscustomobject]@{ sha = ('3' * 40) } }
            '^https://api.github.com/repos/snapetech-org/winget-pkgs/git/commits$' { return [pscustomobject]@{ sha = ('4' * 40) } }
            '^https://api.github.com/repos/snapetech-org/winget-pkgs/git/refs$' {
                if ($global:SlskrWingetTestCase -eq 'ref-failure') { throw 'Ref creation denied' }
                return [pscustomobject]@{ ref = 'refs/heads/slskr-release-9.8.7' }
            }
            '^https://api.github.com/repos/microsoft/winget-pkgs/pulls\?' {
                if ($global:SlskrWingetTestCase -eq 'existing') {
                    return [pscustomobject]@{ state = 'open'; html_url = 'https://github.com/microsoft/winget-pkgs/pull/123' }
                }
                return @()
            }
            '^https://api.github.com/repos/microsoft/winget-pkgs/contents/.github/PULL_REQUEST_TEMPLATE.md$' {
                return [pscustomobject]@{ content = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('PR template')) }
            }
            '^https://api.github.com/repos/microsoft/winget-pkgs/pulls$' {
                return [pscustomobject]@{ state = 'open'; html_url = 'https://github.com/microsoft/winget-pkgs/pull/123' }
            }
            default { throw "Unexpected GitHub request: $Method $Uri" }
        }
    }
    foreach ($case in @('new', 'existing', 'mismatch', 'ref-failure')) {
        $global:SlskrWingetTestCase = $case
        $global:SlskrWingetTestRequests = [Collections.Generic.List[object]]::new()
        $caught = $null
        try { & (Join-Path $PSScriptRoot 'submit-winget-release.ps1') -SubmitPath $root -PackageVersion '9.8.7' 6>$null }
        catch { $caught = $_ }
        $writes = @($global:SlskrWingetTestRequests | Where-Object Method -ne 'GET')
        if (@($writes | Where-Object Method -ne 'POST').Count -ne 0) { throw 'Publisher updated or deleted published history' }
        if ($case -in @('new', 'existing') -and $null -ne $caught) { throw $caught }
        if ($case -in @('mismatch', 'ref-failure') -and $null -eq $caught) { throw 'Unsafe submission failure was ignored' }
        if ($case -in @('existing', 'mismatch') -and $writes.Count -ne 0) { throw 'Existing release branch was overwritten or duplicated' }
        if ($case -eq 'ref-failure' -and @($writes | Where-Object Uri -eq 'https://api.github.com/repos/microsoft/winget-pkgs/pulls').Count -ne 0) { throw 'Opened PR after failed branch creation' }
        if ($case -eq 'new') {
            if ($writes.Count -ne 4) { throw 'Unexpected submission write count' }
            $tree = $writes[0].Body | ConvertFrom-Json
            if ($tree.base_tree -ne ('2' * 40) -or $tree.tree.Count -ne 3) { throw 'Wrong upstream tree or manifest count' }
            if (@($tree.tree | Where-Object { $_.path -notlike 'manifests/s/snapetech/slskr/9.8.7/*.yaml' }).Count -ne 0) { throw 'PR includes other packages or workflow files' }
            $commit = $writes[1].Body | ConvertFrom-Json
            if ($commit.parents.Count -ne 1 -or $commit.parents[0] -ne ('1' * 40)) { throw 'Commit is not based directly on upstream' }
            $ref = $writes[2].Body | ConvertFrom-Json
            if ($ref.ref -ne 'refs/heads/slskr-release-9.8.7' -or $ref.sha -ne ('4' * 40)) { throw 'Wrong new release branch' }
            $pr = $writes[3].Body | ConvertFrom-Json
            if ($pr.head -ne 'snapetech-org:slskr-release-9.8.7' -or $pr.base -ne 'master') { throw 'Wrong canonical fork or PR base' }
        }
    }
    Write-Host 'Winget canonical writes, clean upstream parent, idempotency, content mismatch, and ref-failure tests passed.'
}
finally {
    $env:WINGETCREATE_GITHUB_TOKEN = $originalToken
    $env:GITHUB_STEP_SUMMARY = $originalSummary
    Remove-Item -LiteralPath $root -Recurse -Force
}
