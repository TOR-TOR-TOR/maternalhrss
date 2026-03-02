function Show-Tree {
    param(
        [string]$Path = '.',
        [string]$Prefix = ''
    )

    $items = Get-ChildItem -LiteralPath $Path | Sort-Object { -not $_.PSIsContainer }, Name

    for ($i = 0; $i -lt $items.Count; $i++) {
        $item = $items[$i]
        $connector = '|-- '
        $line = "$Prefix$connector$item"

        # Print to terminal
        Write-Output $line

        # Save to file
        Add-Content -Path "project-structure.txt" -Value $line
   	
        if ($item.PSIsContainer) {
            $newPrefix = "$Prefix|   "
            Show-Tree -Path $item.FullName -Prefix $newPrefix
        }
    }
}

# Clear old file if exists
if (Test-Path "project-structure.txt") {
    Remove-Item "project-structure.txt"
}

# Get root folder name
$rootFolder = Split-Path -Leaf (Get-Location)

# Print root folder name to terminal and file
Write-Output $rootFolder
Add-Content -Path "project-structure.txt" -Value $rootFolder

# Start tree rendering
Show-Tree
