param(
  [string]$ConfigPath = "config/prod.json"
)

$env:OPENCLAW_CONFIG_PATH = $ConfigPath
python -m uv run cdk.cmd synth
