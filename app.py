from __future__ import annotations

import json
import os
from pathlib import Path

import aws_cdk as cdk
from dotenv import load_dotenv

from stacks.lightsail_openclaw_stack import LightsailOpenClawStack, OpenClawConfig


load_dotenv(override=False)


def load_config() -> dict:
    config_path = os.getenv("OPENCLAW_CONFIG_PATH", "config/dev.json")
    resolved = Path(config_path).resolve()

    if not resolved.exists():
        raise FileNotFoundError(
            f"Config file not found: {resolved}. Set OPENCLAW_CONFIG_PATH to a valid JSON file."
        )

    if not resolved.is_file():
        raise ValueError(f"Config path is not a file: {resolved}")

    with resolved.open("r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError as error:
            raise ValueError(f"Config file is not valid JSON: {resolved}") from error


app = cdk.App()
cfg = load_config()

stack_name = cfg.get("stack_name", "OpenClawLightsailStack")
account = cfg.get("account") or os.getenv("CDK_DEFAULT_ACCOUNT")
region = cfg.get("region") or os.getenv("CDK_DEFAULT_REGION")

if not account or not region:
    raise ValueError(
        "Account and region are required. Set them in config/dev.json or through CDK_DEFAULT_ACCOUNT/CDK_DEFAULT_REGION."
    )

openclaw_config = OpenClawConfig.from_dict(cfg)

LightsailOpenClawStack(
    app,
    stack_name,
    env=cdk.Environment(account=account, region=region),
    config=openclaw_config,
)

app.synth()
