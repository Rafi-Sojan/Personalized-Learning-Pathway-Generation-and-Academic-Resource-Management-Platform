param(
    [string]$BaseUrl = "http://host.docker.internal:8000"
)

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is required for the OWASP ZAP baseline scan"
}

$workspace = (Get-Location).Path
docker run --rm -t --mount "type=bind,source=$workspace,target=/zap/wrk" owasp/zap2docker-stable zap-baseline.py -t $BaseUrl -r /zap/wrk/zap-report.html
