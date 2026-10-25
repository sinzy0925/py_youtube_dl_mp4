# YouTube channel batch download
$python = Join-Path $PSScriptRoot '.venv\scripts\python.exe'
$script = Join-Path $PSScriptRoot 'download_channel.py'
$cookies = Join-Path $PSScriptRoot 'cookies.txt'

function Get-DownloadCountFromOutput {
    param([object[]]$Output)
    foreach ($line in $Output) {
        $text = if ($line -is [string]) { $line } else { $line.ToString() }
        if ($text -match 'DOWNLOAD_COUNT:\s*(\d+)') {
            return [int]$Matches[1]
        }
    }
    return 0
}

function Invoke-ChannelDownload {
    param(
        [string]$Channel,
        [string]$StartEnd,
        [switch]$ContinueOnError
    )
    $output = @(
        & $python $script $Channel --startend $StartEnd --cookies $cookies 2>&1
    )
    $output | ForEach-Object { Write-Host $_ }
    $count = Get-DownloadCountFromOutput $output
    if ($LASTEXITCODE -ne 0) {
        if ($ContinueOnError) {
            return $count
        }
        exit $LASTEXITCODE
    }
    return $count
}

$phase0Total = 0
$phase0Total += Invoke-ChannelDownload '@boherteck2585' '0:0' -ContinueOnError
$phase0Total += Invoke-ChannelDownload '@misterzafar' '0:0' -ContinueOnError
$phase0Total += Invoke-ChannelDownload '@AnnuMusicCentre' '0:0' -ContinueOnError
$phase0Total += Invoke-ChannelDownload '@faitatosp5823' '0:0' -ContinueOnError
$phase0Total += Invoke-ChannelDownload '@UjanNews-Yt' '0:0' -ContinueOnError

if ($phase0Total -eq 0) {
    Write-Host ''
    Write-Host '最初の4件でダウンロードが1度も発生しなかったため、以降をスキップします。'
    exit 0
}

$null = Invoke-ChannelDownload '@boherteck2585' '1:1'
$null = Invoke-ChannelDownload '@misterzafar' '1:1'
$null = Invoke-ChannelDownload '@AnnuMusicCentre' '1:1'
$null = Invoke-ChannelDownload '@UjanNews-Yt' '1:1'
$null = Invoke-ChannelDownload '@faitatosp5823' '1:1'

$null = Invoke-ChannelDownload '@boherteck2585' '2:2'
$null = Invoke-ChannelDownload '@misterzafar' '2:2'
$null = Invoke-ChannelDownload '@AnnuMusicCentre' '2:2'
$null = Invoke-ChannelDownload '@UjanNews-Yt' '2:2'
$null = Invoke-ChannelDownload '@faitatosp5823' '2:2'