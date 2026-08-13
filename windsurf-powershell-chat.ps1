{ $_ -like '/open *' } {
    $path = $input.Substring(6).Trim()
    if (-not $path) {
        Write-Host "Usage: /open <path>" -ForegroundColor Yellow
        continue
    }
    Write-Host "Opening: $path" -ForegroundColor Gray
    code $path
}
