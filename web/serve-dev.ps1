# FacultyLink reviewer/admin static site (development).
# Port 8080 is often used by other software (e.g. Apache httpd); default here is 8081.
param([int]$Port = 8081)
Set-Location $PSScriptRoot
Write-Host "Serving FacultyLink web from $PWD on http://127.0.0.1:$Port/"
Write-Host "Login: http://127.0.0.1:$Port/pages/public/login.html"
python -m http.server $Port --bind 127.0.0.1
