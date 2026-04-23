from __future__ import annotations

from dataclasses import dataclass
import ipaddress
from pathlib import Path
import re

from aws_cdk import CfnOutput, CfnTag, CustomResource, Duration, Stack
from aws_cdk import custom_resources as cr
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk.aws_lightsail import (
    CfnInstance,
    CfnStaticIp,
)
from constructs import Construct


@dataclass(frozen=True)
class OpenClawConfig:
    stack_name: str
    region: str
    account: str
    instance_name: str
    static_ip_name: str
    blueprint_id: str
    bundle_id: str
    availability_zone: str
    key_pair_name: str
    ssh_cidr: str
    enable_auto_snapshot: bool
    snapshot_time_of_day_utc: str
    tags: dict[str, str]

    @classmethod
    def from_dict(cls, raw: dict) -> "OpenClawConfig":
        region = raw["region"]
        config = cls(
            stack_name=raw.get("stack_name", "OpenClawLightsailStack"),
            region=region,
            account=raw["account"],
            instance_name=raw.get("instance_name", "openclaw-dev"),
            static_ip_name=raw.get("static_ip_name", "openclaw-dev-ip"),
            blueprint_id=raw.get("blueprint_id", "openclaw_ls_1_0"),
            bundle_id=raw.get("bundle_id", "medium_3_0"),
            availability_zone=raw.get("availability_zone", f"{region}a"),
            key_pair_name=raw["key_pair_name"],
            ssh_cidr=raw.get("ssh_cidr", "0.0.0.0/0"),
            enable_auto_snapshot=raw.get("enable_auto_snapshot", False),
            snapshot_time_of_day_utc=raw.get("snapshot_time_of_day_utc", "03:00"),
            tags=raw.get(
                "tags",
                {
                    "project": "openclaw",
                    "env": "dev",
                    "owner": "r3xakead0",
                    "managed-by": "cdk",
                },
            ),
        )
        config._validate()
        return config

    def _validate(self) -> None:
        if not re.fullmatch(r"\d{12}", self.account):
            raise ValueError("'account' must be a 12-digit AWS account ID")

        if not re.fullmatch(r"[a-z]{2}-[a-z]+-\d", self.region):
            raise ValueError(f"'region' has invalid format: {self.region}")

        if not re.fullmatch(rf"{re.escape(self.region)}[a-z]", self.availability_zone):
            raise ValueError(
                f"'availability_zone' must belong to region '{self.region}', got '{self.availability_zone}'"
            )

        if not self.key_pair_name.strip():
            raise ValueError("'key_pair_name' cannot be empty")

        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", self.snapshot_time_of_day_utc):
            raise ValueError(
                "'snapshot_time_of_day_utc' must use 24h UTC format HH:MM (example: 03:00)"
            )

        try:
            ipaddress.ip_network(self.ssh_cidr, strict=False)
        except ValueError as error:
            raise ValueError(f"'ssh_cidr' is not a valid CIDR block: {self.ssh_cidr}") from error

        if not self.tags:
            raise ValueError("'tags' cannot be empty")

        invalid_tag_keys = [key for key in self.tags.keys() if not isinstance(key, str) or not key.strip()]
        if invalid_tag_keys:
            raise ValueError("'tags' keys must be non-empty strings")

        invalid_tag_values = [
            value for value in self.tags.values() if not isinstance(value, str) or not value.strip()
        ]
        if invalid_tag_values:
            raise ValueError("'tags' values must be non-empty strings")


class LightsailOpenClawStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: OpenClawConfig, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        tags = [CfnTag(key=k, value=v) for k, v in config.tags.items()]

        instance_add_ons = None
        if config.enable_auto_snapshot:
            instance_add_ons = [
                CfnInstance.AddOnProperty(
                    add_on_type="AutoSnapshot",
                    auto_snapshot_add_on_request=CfnInstance.AutoSnapshotAddOnProperty(
                        snapshot_time_of_day=config.snapshot_time_of_day_utc
                    ),
                )
            ]

        instance = CfnInstance(
            self,
            "OpenClawInstance",
            instance_name=config.instance_name,
            blueprint_id=config.blueprint_id,
            bundle_id=config.bundle_id,
            availability_zone=config.availability_zone,
            key_pair_name=config.key_pair_name,
            networking=CfnInstance.NetworkingProperty(
                ports=[
                    CfnInstance.PortProperty(
                        from_port=22,
                        to_port=22,
                        protocol="tcp",
                        cidrs=[config.ssh_cidr],
                    ),
                    CfnInstance.PortProperty(
                        from_port=80,
                        to_port=80,
                        protocol="tcp",
                        cidrs=["0.0.0.0/0"],
                    ),
                    CfnInstance.PortProperty(
                        from_port=443,
                        to_port=443,
                        protocol="tcp",
                        cidrs=["0.0.0.0/0"],
                    ),
                ]
            ),
            add_ons=instance_add_ons,
            tags=tags,
        )

        static_ip = CfnStaticIp(
            self,
            "OpenClawStaticIp",
            static_ip_name=config.static_ip_name,
        )

        static_ip_attachment = cr.AwsCustomResource(
            self,
            "OpenClawStaticIpAttachment",
            install_latest_aws_sdk=False,
            on_create=cr.AwsSdkCall(
                service="Lightsail",
                action="attachStaticIp",
                parameters={
                    "instanceName": config.instance_name,
                    "staticIpName": config.static_ip_name,
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    f"{config.static_ip_name}-attachment"
                ),
            ),
            on_update=cr.AwsSdkCall(
                service="Lightsail",
                action="attachStaticIp",
                parameters={
                    "instanceName": config.instance_name,
                    "staticIpName": config.static_ip_name,
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    f"{config.static_ip_name}-attachment"
                ),
            ),
            on_delete=cr.AwsSdkCall(
                service="Lightsail",
                action="detachStaticIp",
                parameters={
                    "staticIpName": config.static_ip_name,
                },
            ),
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
        )
        static_ip_attachment.node.add_dependency(instance)
        static_ip_attachment.node.add_dependency(static_ip)

        bedrock_role_handler = _lambda.Function(
            self,
            "OpenClawBedrockRoleSetupHandler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.on_event",
            timeout=Duration.seconds(120),
            code=_lambda.Code.from_asset(
                str(Path(__file__).resolve().parents[1] / "lambda" / "bedrock_role_setup")
            ),
        )
        bedrock_role_handler.add_to_role_policy(
            iam.PolicyStatement(
                actions=["lightsail:GetInstance"],
                resources=["*"],
            )
        )
        bedrock_role_handler.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "iam:CreateRole",
                    "iam:DeleteRole",
                    "iam:DeleteRolePolicy",
                    "iam:GetRole",
                    "iam:PutRolePolicy",
                    "iam:UpdateAssumeRolePolicy",
                ],
                resources=["*"],
            )
        )
        bedrock_role_handler.add_to_role_policy(
            iam.PolicyStatement(
                actions=["sts:GetCallerIdentity"],
                resources=["*"],
            )
        )

        bedrock_role_provider = cr.Provider(
            self,
            "OpenClawBedrockRoleSetupProvider",
            on_event_handler=bedrock_role_handler,
        )

        bedrock_role_setup = CustomResource(
            self,
            "OpenClawBedrockRoleSetup",
            service_token=bedrock_role_provider.service_token,
            properties={
                "InstanceName": config.instance_name,
                "Region": config.region,
                "InstanceArnHint": instance.attr_instance_arn,
            },
        )
        bedrock_role_setup.node.add_dependency(instance)
        CfnOutput(
            self,
            "BedrockRoleArn",
            value=bedrock_role_setup.get_att_string("RoleArn"),
        )

        CfnOutput(self, "InstanceName", value=instance.instance_name)
        CfnOutput(self, "StaticIpName", value=static_ip.static_ip_name)
        CfnOutput(self, "PublicIp", value=static_ip.attr_ip_address)
