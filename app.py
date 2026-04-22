from __future__ import annotations

import json
import os
from pathlib import Path

import aws_cdk as cdk

from stacks.lightsail_openclaw_stack import LightsailOpenClawStack, OpenClawConfig


def load_config() -> dict:
    config_path = os.getenv("OPENCLAW_CONFIG_PATH", "config/dev.json")
    resolved = Path(config_path).resolve()
    with resolved.open("r", encoding="utf-8") as file:
        return json.load(file)


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
