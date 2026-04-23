param(
  [string]$ConfigPath = "config/prod.json"
)

$env:OPENCLAW_CONFIG_PATH = $ConfigPath
uv run cdk synth
