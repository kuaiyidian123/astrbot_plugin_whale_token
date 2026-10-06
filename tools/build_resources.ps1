# Build compressed ticket-face images for the AstrBot plugin.
# Source: ..\..\DeepSeek-Token-Bank\dist\png (7560x3528 originals)
# Output: ..\resources\*.jpg
# Requires only Windows PowerShell 5 + .NET System.Drawing (no Pillow, no network).

Add-Type -AssemblyName System.Drawing

$pluginRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $pluginRoot
$srcDir = Join-Path $repoRoot 'DeepSeek-Token-Bank\dist\png'
$outDir = Join-Path $pluginRoot 'resources'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# denom key -> note length in mm (used to keep the real relative size difference)
$denoms = [ordered]@{
  '010000000' = 132.0
  '020000000' = 142.0
  '050000000' = 148.0
  '100000000' = 150.0
  '200000000' = 158.0
  '500000000' = 176.0
}

$baseWidth = 1400      # width in px of the 150mm reference note
$ratio = 70.0 / 150.0  # face height / face width (constant across the series)
$quality = 88L

$encoder = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() |
  Where-Object { $_.MimeType -eq 'image/jpeg' }

function Save-ScaledJpeg($srcFile, $outFile, $width, $height, $qualityValue) {
  $img = [System.Drawing.Image]::FromFile($srcFile)
  $bmp = New-Object System.Drawing.Bitmap($width, $height)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
  $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
  $g.DrawImage($img, 0, 0, $width, $height)
  $params = New-Object System.Drawing.Imaging.EncoderParameters(1)
  $params.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter(
    [System.Drawing.Imaging.Encoder]::Quality, [long]$qualityValue)
  $bmp.Save($outFile, $encoder, $params)
  $g.Dispose(); $bmp.Dispose(); $img.Dispose()
}

foreach ($face in @('front', 'back')) {
  foreach ($key in $denoms.Keys) {
    $srcFile = Join-Path $srcDir ("{0}_{1}.png" -f $face, $key)
    if (-not (Test-Path $srcFile)) { Write-Host "missing: $srcFile"; continue }
    $w = [int][math]::Round($baseWidth * $denoms[$key] / 150.0)
    $h = [int][math]::Round($w * $ratio)
    $outFile = Join-Path $outDir ("{0}_{1}.jpg" -f $face, $key)
    Save-ScaledJpeg $srcFile $outFile $w $h $quality
    Write-Host ("{0} -> {1}x{2}" -f (Split-Path -Leaf $outFile), $w, $h)
  }
}

# Full-series overview poster (very long image -> downscale hard)
$series = Join-Path $repoRoot 'DeepSeek-Token-Bank\dist\series-all.png'
if (Test-Path $series) {
  $img = [System.Drawing.Image]::FromFile($series)
  $w = 900
  $h = [int][math]::Round($img.Height * $w / $img.Width)
  $img.Dispose()
  $outFile = Join-Path $outDir 'series-all.jpg'
  Save-ScaledJpeg $series $outFile $w $h 85
  Write-Host ("series-all.jpg -> {0}x{1}" -f $w, $h)
}

Write-Host "done."
