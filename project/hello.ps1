Write-Output "Hello"

# Get the path of the script itself
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$imagePath = Join-Path $scriptDir "1.jpg"

# Print the image
Start-Process -FilePath $imagePath -Verb Print
