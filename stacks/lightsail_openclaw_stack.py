from __future__ import annotations

from dataclasses import dataclass

from aws_cdk import CfnOutput, CfnTag, Stack
from aws_cdk import custom_resources as cr
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
    snapshot_time_of_day_utc: str
    tags: dict[str, str]

    @classmethod
    def from_dict(cls, raw: dict) -> "OpenClawConfig":
        region = raw["region"]

        return cls(
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
            snapshot_time_of_day_utc=raw.get("snapshot_time_of_day_utc", "03:00"),
            tags=raw.get(
                "tags",
                {
                    "project": "openclaw",
                    "env": "dev",
                    "managed-by": "cdk",
                },
            ),
        )


class LightsailOpenClawStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: OpenClawConfig, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        tags = [CfnTag(key=k, value=v) for k, v in config.tags.items()]

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
            add_ons=[
                CfnInstance.AddOnProperty(
                    add_on_type="AutoSnapshot",
                    auto_snapshot_add_on_request=CfnInstance.AutoSnapshotAddOnProperty(
                        snapshot_time_of_day=config.snapshot_time_of_day_utc
                    ),
                )
            ],
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

        CfnOutput(self, "InstanceName", value=instance.instance_name)
        CfnOutput(self, "StaticIpName", value=static_ip.static_ip_name)
        CfnOutput(self, "PublicIp", value=static_ip.attr_ip_address)
