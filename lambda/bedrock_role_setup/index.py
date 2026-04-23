import json

import boto3
from botocore.exceptions import ClientError


def _trust_policy(lightsail_account: str, instance_id: str) -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:sts::{lightsail_account}:assumed-role/AmazonLightsailInstance/{instance_id}",
                },
                "Action": "sts:AssumeRole",
            }
        ],
    }


def _permissions_policy() -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "BedrockInvoke",
                "Effect": "Allow",
                "Action": [
                    "bedrock:ListFoundationModels",
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                "Resource": "*",
            },
            {
                "Sid": "MarketplaceModelAccess",
                "Effect": "Allow",
                "Action": [
                    "aws-marketplace:Subscribe",
                    "aws-marketplace:Unsubscribe",
                    "aws-marketplace:ViewSubscriptions",
                ],
                "Resource": "*",
            },
        ],
    }


def _upsert_role(instance_name: str, region: str) -> dict:
    lightsail = boto3.client("lightsail", region_name=region)
    iam = boto3.client("iam")
    sts = boto3.client("sts")

    support_code = lightsail.get_instance(instanceName=instance_name)["instance"]["supportCode"]
    if not support_code or "/" not in support_code:
        raise ValueError(f"Invalid support code for instance '{instance_name}': {support_code}")

    lightsail_account, instance_id = support_code.split("/", 1)
    role_name = f"LightsailRoleFor-{instance_id}"
    trust_policy = _trust_policy(lightsail_account, instance_id)

    try:
        iam.get_role(RoleName=role_name)
        iam.update_assume_role_policy(RoleName=role_name, PolicyDocument=json.dumps(trust_policy))
    except ClientError as error:
        if error.response["Error"].get("Code") != "NoSuchEntity":
            raise
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f"Allows OpenClaw on Lightsail instance {instance_name} to access Bedrock",
        )

    iam.put_role_policy(
        RoleName=role_name,
        PolicyName="OpenClawBedrockAccess",
        PolicyDocument=json.dumps(_permissions_policy()),
    )

    account_id = sts.get_caller_identity()["Account"]
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    return {"RoleName": role_name, "RoleArn": role_arn, "InstanceId": instance_id}


def _delete_role(role_name: str) -> None:
    if not role_name:
        return

    iam = boto3.client("iam")
    try:
        iam.delete_role_policy(RoleName=role_name, PolicyName="OpenClawBedrockAccess")
    except ClientError as error:
        if error.response["Error"].get("Code") != "NoSuchEntity":
            raise

    try:
        iam.delete_role(RoleName=role_name)
    except ClientError as error:
        if error.response["Error"].get("Code") != "NoSuchEntity":
            raise


def on_event(event, _context):
    request_type = event["RequestType"]
    props = event.get("ResourceProperties", {})

    if request_type in ("Create", "Update"):
        result = _upsert_role(
            instance_name=props["InstanceName"],
            region=props["Region"],
        )
        return {
            "PhysicalResourceId": result["RoleName"],
            "Data": result,
        }

    _delete_role(event.get("PhysicalResourceId", ""))

    return {
        "PhysicalResourceId": event.get("PhysicalResourceId", "deleted"),
        "Data": {},
    }
