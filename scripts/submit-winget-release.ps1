[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $SubmitPath,

    [Parameter(Mandatory = $true)]
    [string] $PackageVersion
)

$ErrorActionPreference = 'Stop'

$token = $env:WINGETCREATE_GITHUB_TOKEN
if ([string]::IsNullOrWhiteSpace($token)) {
    throw 'WINGETCREATE_GITHUB_TOKEN is required to submit the Winget manifest.'
}

if ($PackageVersion -notmatch '^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$') {
    throw "Invalid Winget package version: $PackageVersion"
}

if (-not (Test-Path -LiteralPath $SubmitPath -PathType Container)) {
    throw "Winget manifest directory not found: $SubmitPath"
}

$apiRoot = 'https://api.github.com'
$headers = @{
    Authorization = "Bearer $token"
    Accept = 'application/vnd.github+json'
    'X-GitHub-Api-Version' = '2022-11-28'
    'User-Agent' = 'slskr-release'
}

function Get-HttpStatusCode {
    param(
        [Parameter(Mandatory = $true)]
        [System.Management.Automation.ErrorRecord] $ErrorRecord
    )

    $response = $ErrorRecord.Exception.Response
    if ($null -ne $response) {
        try {
            return [int]$response.StatusCode
        }
        catch {
            return 0
        }
    }

    return 0
}

function Invoke-GitHubApi {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('GET', 'POST')]
        [string] $Method,

        [Parameter(Mandatory = $true)]
        [string] $Uri,

        [Parameter(Mandatory = $false)]
        [AllowNull()]
        [object] $Body
    )

    $request = @{
        Method = $Method
        Uri = $Uri
        Headers = $headers
        ErrorAction = 'Stop'
    }
    if ($PSBoundParameters.ContainsKey('Body')) {
        $request.Body = $Body | ConvertTo-Json -Depth 20 -Compress
        $request.ContentType = 'application/json'
    }

    Invoke-RestMethod @request
}

function Escape-PathSegment {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Value
    )

    [Uri]::EscapeDataString($Value)
}

$user = Invoke-GitHubApi -Method GET -Uri "$apiRoot/user"
$owner = [string]$user.login
if ([string]::IsNullOrWhiteSpace($owner)) {
    throw 'GitHub token did not identify an account.'
}

$upstream = Invoke-GitHubApi -Method GET -Uri "$apiRoot/repos/microsoft/winget-pkgs"
$upstreamBranch = [string]$upstream.default_branch
$upstreamRef = Invoke-GitHubApi -Method GET -Uri "$apiRoot/repos/microsoft/winget-pkgs/git/ref/heads/$(Escape-PathSegment $upstreamBranch)"
$upstreamSha = [string]$upstreamRef.object.sha
if ([string]::IsNullOrWhiteSpace($upstreamSha)) {
    throw "Unable to resolve microsoft/winget-pkgs/$upstreamBranch."
}

$forkUri = "$apiRoot/repos/$owner/winget-pkgs"
$fork = $null
try {
    $fork = Invoke-GitHubApi -Method GET -Uri $forkUri
}
catch {
    if ((Get-HttpStatusCode $_) -ne 404) {
        throw
    }

    Write-Host "Creating $owner/winget-pkgs fork."
    $null = Invoke-GitHubApi -Method POST -Uri "$apiRoot/repos/microsoft/winget-pkgs/forks" -Body @{}
    for ($poll = 1; $poll -le 12; $poll++) {
        Start-Sleep -Seconds 5
        try {
            $fork = Invoke-GitHubApi -Method GET -Uri $forkUri
            break
        }
        catch {
            if ((Get-HttpStatusCode $_) -ne 404 -or $poll -eq 12) {
                throw
            }
        }
    }
}

if ($null -eq $fork) {
    throw "GitHub fork was not available after creation: $forkUri"
}

# GitHub may redirect the authenticated user's repository URL to a fork owned
# by an organization. Resolve the canonical owner before any write request:
# redirects can turn authenticated POSTs into unauthenticated requests.
$forkOwner = [string]$fork.owner.login
if ([string]::IsNullOrWhiteSpace($forkOwner) -or [string]$fork.name -ne 'winget-pkgs') {
    throw "GitHub returned an unexpected Winget fork: $($fork.full_name)"
}
$owner = $forkOwner
$forkUri = "$apiRoot/repos/$owner/winget-pkgs"

# Create the final manifest commit directly on a new branch from upstream.
# Canonical repository URLs avoid authenticated-write redirects in clients that
# address Git data through /repositories/<id>. Never reset the fork default.
$branch = "slskr-release-$PackageVersion"
$branchPath = Escape-PathSegment $branch
$manifestRoot = "manifests/s/snapetech/slskr/$PackageVersion"
$expectedNames = @('snapetech.slskr.yaml', 'snapetech.slskr.installer.yaml', 'snapetech.slskr.locale.en-US.yaml')
$files = @(Get-ChildItem -LiteralPath $SubmitPath -File)
if ($files.Count -ne 3 -or @(Compare-Object ($files.Name | Sort-Object) ($expectedNames | Sort-Object)).Count -ne 0) {
    throw 'Expected exactly the three snapetech.slskr manifests.'
}
function Read-ManifestText {
    param([string] $Path)
    [IO.File]::ReadAllText($Path).Replace("`r`n", "`n").Replace("`n", "`r`n")
}
$existingRef = $null
try { $existingRef = Invoke-GitHubApi -Method GET -Uri "$forkUri/git/ref/heads/$branchPath" }
catch { if ((Get-HttpStatusCode $_) -ne 404) { throw } }
if ($null -ne $existingRef) {
    foreach ($file in $files) {
        $remote = Invoke-GitHubApi -Method GET -Uri "$forkUri/contents/$manifestRoot/$($file.Name)?ref=$branchPath"
        $remoteText = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($remote.content))
        if ($remoteText.Replace("`r`n", "`n") -cne (Read-ManifestText $file.FullName).Replace("`r`n", "`n")) {
            throw "Existing release branch has different manifest content: $branch. Preserve it and investigate."
        }
    }
}
else {
    $upstreamCommit = Invoke-GitHubApi -Method GET -Uri "$apiRoot/repos/microsoft/winget-pkgs/git/commits/$upstreamSha"
    $treeEntries = @($files | ForEach-Object {
        @{ path = "$manifestRoot/$($_.Name)"; mode = '100644'; type = 'blob'; content = (Read-ManifestText $_.FullName) }
    })
    $tree = Invoke-GitHubApi -Method POST -Uri "$forkUri/git/trees" -Body @{
        base_tree = $upstreamCommit.tree.sha
        tree = $treeEntries
    }
    $commit = Invoke-GitHubApi -Method POST -Uri "$forkUri/git/commits" -Body @{
        message = "New version: snapetech.slskr version $PackageVersion"
        tree = $tree.sha
        parents = @($upstreamSha)
    }
    $null = Invoke-GitHubApi -Method POST -Uri "$forkUri/git/refs" -Body @{
        ref = "refs/heads/$branch"
        sha = $commit.sha
    }
}
$head = [Uri]::EscapeDataString("${owner}:$branch")
$existingPrs = @(Invoke-GitHubApi -Method GET -Uri "$apiRoot/repos/microsoft/winget-pkgs/pulls?state=all&head=$head")
if ($existingPrs.Count -gt 0) {
    $pr = $existingPrs[0]
    if ($pr.state -ne 'open' -and -not $pr.merged_at) {
        throw "The existing Winget release PR was closed without merging: $($pr.html_url)"
    }
}
else {
    $template = Invoke-GitHubApi -Method GET -Uri "$apiRoot/repos/microsoft/winget-pkgs/contents/.github/PULL_REQUEST_TEMPLATE.md"
    $body = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($template.content))
    $body += "`n`nRelease validation: the published Windows archive checksum, CLI version smoke, and Microsoft Defender archive/extracted-file scans passed in the slskr release workflow. This PR changes only snapetech.slskr $PackageVersion manifests.`n"
    $pr = Invoke-GitHubApi -Method POST -Uri "$apiRoot/repos/microsoft/winget-pkgs/pulls" -Body @{
        title = "New version: snapetech.slskr version $PackageVersion"
        head = "${owner}:$branch"
        base = $upstreamBranch
        body = $body
    }
}
Write-Host "Winget pull request: $($pr.html_url)"
if ($env:GITHUB_STEP_SUMMARY) {
    Add-Content $env:GITHUB_STEP_SUMMARY "Winget submission: [$PackageVersion]($($pr.html_url))"
}
