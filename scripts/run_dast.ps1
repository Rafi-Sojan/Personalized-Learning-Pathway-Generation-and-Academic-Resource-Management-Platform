param(
    [string]$BaseUrl = "http://host.docker.internal:8000"
)

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is required for the OWASP ZAP baseline scan"
}

$workspace = (Get-Location).Path
docker run --rm -t --user 0 --mount "type=bind,source=$workspace,target=/zap/wrk" ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t $BaseUrl -r /zap/wrk/zap-report.html -J /zap/wrk/zap-report.json
