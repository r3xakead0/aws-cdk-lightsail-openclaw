from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from stacks.lightsail_openclaw_stack import OpenClawConfig


def _base_config() -> dict:
    return {
        "stack_name": "OpenClawLightsailStack",
        "account": "142728997126",
        "region": "us-east-1",
        "instance_name": "openclaw-dev-v1",
        "static_ip_name": "openclaw-dev-ip",
        "blueprint_id": "openclaw_ls_1_0",
        "bundle_id": "medium_3_0",
        "availability_zone": "us-east-1a",
        "key_pair_name": "openclaw-dev-key",
        "ssh_cidr": "0.0.0.0/0",
        "enable_auto_snapshot": False,
        "snapshot_time_of_day_utc": "03:00",
        "tags": {
            "project": "openclaw",
            "env": "dev",
            "owner": "r3xakead0",
            "managed-by": "cdk",
        },
    }


def test_from_dict_loads_tags_from_json_payload() -> None:
    raw = _base_config()
    raw["tags"] = {"env": "prod", "owner": "team-platform"}

    config = OpenClawConfig.from_dict(raw)

    assert config.tags == {"env": "prod", "owner": "team-platform"}


def test_from_dict_applies_expected_defaults() -> None:
    raw = {
        "account": "142728997126",
        "region": "us-east-1",
        "key_pair_name": "openclaw-dev-key",
    }

    config = OpenClawConfig.from_dict(raw)

    assert config.stack_name == "OpenClawLightsailStack"
    assert config.instance_name == "openclaw-dev"
    assert config.static_ip_name == "openclaw-dev-ip"
    assert config.blueprint_id == "openclaw_ls_1_0"
    assert config.bundle_id == "medium_3_0"
    assert config.availability_zone == "us-east-1a"
    assert config.ssh_cidr == "0.0.0.0/0"
    assert config.enable_auto_snapshot is False
    assert config.snapshot_time_of_day_utc == "03:00"
    assert config.tags == {
        "project": "openclaw",
        "env": "dev",
        "owner": "r3xakead0",
        "managed-by": "cdk",
    }


def test_from_dict_raises_for_missing_required_fields() -> None:
    raw = _base_config()
    del raw["region"]
    with pytest.raises(KeyError, match="'region'"):
        OpenClawConfig.from_dict(raw)

    raw = _base_config()
    del raw["account"]
    with pytest.raises(KeyError, match="'account'"):
        OpenClawConfig.from_dict(raw)

    raw = _base_config()
    del raw["key_pair_name"]
    with pytest.raises(KeyError, match="'key_pair_name'"):
        OpenClawConfig.from_dict(raw)
