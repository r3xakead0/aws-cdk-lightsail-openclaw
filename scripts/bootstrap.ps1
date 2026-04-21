param(
  [string]$AccountId,
  [string]$Region
)

if (-not $AccountId -or -not $Region) {
  throw "Uso: ./scripts/bootstrap.ps1 -AccountId <ACCOUNT_ID> -Region <REGION>"
}

python -m uv run cdk.cmd bootstrap "aws://$AccountId/$Region"
