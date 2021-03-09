import boto3
import botocore
import click
import re
from typing import List
from commands.credentials import get_user_credentials, verify_credentials
from requirements import LeanIXCloudScanAdvisorPolicyReader, LeanIXCloudScanBillingPolicyReader


def check_user_policies(username):
    iam = boto3.client('iam')
    pattern = re.compile('LeanIXCloudScanAdvisorPolicyReader|LeanIXCloudScanBillingPolicyReader')
    policies = iam.list_attached_user_policies(UserName=username)
    user_policies = list()
    print(f"The user {username} has the following policies attached:")
    for policy in policies['AttachedPolicies']:
        policy_arn=policy['PolicyArn']
        print(policy_arn)
        if re.search(pattern,policy_arn):
            user_policies.append(policy_arn)
            

    return user_policies


def authenticated_scan_policies(username: str):
    # assumes that roles are attached directly to user - not via group assignment
    try:
        user_policies = check_user_policies(username=username)
    except botocore.exceptions.NoCredentialsError:
        print("Seems like you're not authenticated. Let's try to authenticate...")
        id, key = get_user_credentials()
        credential_check = verify_credentials(
            aws_access_key_id=id, aws_secret_access_key=key)

        if credential_check:
            user_policies = check_user_policies(username=username)
            

        else:
            print("Authentication failed! Please check credentials")
            user_policies = None

    return user_policies


def verify_policy_permissions(policies: List[str]):
    iam = boto3.client('iam')
    policy_container = dict()
    for policy in policies:
        policy_version = iam.get_policy(PolicyArn=policy)[
            'Policy']['DefaultVersionId']
        permission = iam.get_policy_version(
            PolicyArn=policy,
            VersionId=policy_version)['PolicyVersion']['Document']

        policy_container[policy]=permission
    
    


@click.command()
@click.option('--username', '-u', 'username', required=True,
              help="AWS Username")
def cli(username):
    user_policies = authenticated_scan_policies(username=username)
    verify_policy_permissions(user_policies)
