param(
  [string]$ConfigPath = "config/dev.json"
)

$env:OPENCLAW_CONFIG_PATH = $ConfigPath
uv run cdk synth
