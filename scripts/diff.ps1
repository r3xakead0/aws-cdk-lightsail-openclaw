param(
  [string]$ConfigPath = "config/dev.json"
)

$env:OPENCLAW_CONFIG_PATH = $ConfigPath
python -m uv run cdk.cmd diff
