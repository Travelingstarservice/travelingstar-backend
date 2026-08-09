# Traveling Star API Test Suite (Admin Query Parameter Authentication)
# Admin password: 9404

$adminPassword = "9404"
$baseUrl = "http://travelingstarservice.com"

function Write-Section($text) {
    Write-Host "`n=== $text ===" -ForegroundColor Cyan
}

function Write-Success($text) {
    Write-Host "$text" -ForegroundColor Green
}

function Write-Failure($text) {
    Write-Host "$text" -ForegroundColor Red
}

function Test-Endpoint($name, $path, $method="GET", $body=$null) {
    Write-Section $name

    # Append admin password as query parameter
    $url = "$baseUrl$path?admin=$adminPassword"

    if ($method -eq "POST") {
        $response = C:\Windows\System32\curl.exe -s -X POST $url `
            -H "Accept: application/json" `
            -H "Content-Type: application/json" `
            -d $body
    } else {
        $response = C:\Windows\System32\curl.exe -s $url `
            -H "Accept: application/json"
    }

    if ($response) {
        Write-Success $response
    } else {
        Write-Failure "No response received."
    }
}

# Health Check
Test-Endpoint "Health Check" "/api/test"

# Fleet Dispatch Ops
Test-Endpoint "Fleet Dispatch Ops" "/api/fleet/dispatch/ops"

# Promotions
Test-Endpoint "Promotions" "/api/dispatch/promotions"

# Owner Password Update (POST Example)
Test-Endpoint "Owner Password Update" "/api/owner/password/update" "POST" "{ \"owner_id\": \"123\", \"new_password\": \"MyNewPass123\" }"

# Hotspot Locator
Test-Endpoint "Hotspot Locator" "/api/ai/locate"

Write-Section "All Traveling Star API Tests Complete"
