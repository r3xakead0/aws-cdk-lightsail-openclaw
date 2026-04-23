param(
  [string]$AccountId,
  [string]$Region
)

if (-not $AccountId -or -not $Region) {
  throw "Uso: ./scripts/windows/prod/bootstrap.ps1 -AccountId <ACCOUNT_ID> -Region <REGION>"
}

uv run cdk bootstrap "aws://$AccountId/$Region"
