import boto3
import botocore
import click
import re
from typing import List
from commands.credentials import get_user_credentials, verify_credentials
from requirements import LeanIXCloudScanAdvisorPolicyReader, LeanIXCloudScanBillingPolicyReader


def check_user_policies(username: str):
    """
        gets all AWS policies attached to a user, fetched by his/her AWS username, and checks whether the LeanIX CI Policies 
        were created. This check does not pick up policies via group assignment

    """

    iam = boto3.client('iam')
    pattern = re.compile(
        'LeanIXCloudScanAdvisorPolicyReader|LeanIXCloudScanBillingPolicyReader')
    policies = iam.list_attached_user_policies(UserName=username)
    user_policies = list()

    for policy in policies['AttachedPolicies']:
        policy_arn = policy['PolicyArn']
        if re.search(pattern, policy_arn):
            user_policies.append(policy_arn)

    return user_policies


def check_user_group_policies(username: str):
    iam = boto3.client('iam')
    user_groups_list = iam.list_groups_for_user(UserName=username)['Groups']

    all_attached_groups = list()
    for group in user_groups_list:
        all_attached_groups.append(group['GroupName'])

    group_policies = list()
    for group_policy in all_attached_groups:
        policies = iam.list_attached_group_policies(
            GroupName=str(group_policy))['AttachedPolicies']

        for policy in policies:
            group_policies.append(policy['PolicyArn'])

    return group_policies


def get_all_user_policies(username: str):
    user_policies = check_user_policies(username=username)
    group_assigned_policies = check_user_group_policies(username=username)

    print(f"The user {username} has the following polices attached: \n")
    print("User-Policies:")
    if len(user_policies) == 0:
        print("- \n")
    else:
        print(*user_policies, sep="\n")

    print("Group-assigned Policies:")
    if len(group_assigned_policies) == 0:
        print("- \n")
    else:
        print(*group_assigned_policies, sep="\n")
    print("\n")

    if len(user_policies) == 0:
        all_user_policies = group_assigned_policies
    else:
        all_user_policies = user_policies + group_assigned_policies

    return all_user_policies


def authenticated_scan_policies(username: str):
    """
        gets all AWS policies attached to a user, fetched by his/her AWS username, and checks whether the LeanIX CI Policies 
        were created and authenticates / verifies the credentials, if it fails to query the IAM console.
    """

    # assumes that roles are attached directly to user - not via group assignment
    try:
        user_policies = get_all_user_policies(username=username)
    except botocore.exceptions.NoCredentialsError:
        print("Seems like you're not authenticated. Let's try to authenticate...")
        id, key = get_user_credentials()
        credential_check = verify_credentials(
            aws_access_key_id=id, aws_secret_access_key=key)

        if credential_check:
            user_policies = get_all_user_policies(username=username)

        else:
            print("Authentication failed! Please check credentials")
            user_policies = None

    return user_policies


def compare_with_leanix(policies: dict):
    billing_policies = LeanIXCloudScanBillingPolicyReader
    advisor_policies = LeanIXCloudScanAdvisorPolicyReader

    billing_policy_name="LeanIXCloudScanBillingPolicyReader"
    advisor_policy_name="LeanIXCloudScanAdvisorPolicyReader"

    billing_policy_pat = re.compile(billing_policy_name)
    advisor_policy_pat = re.compile(advisor_policy_name)

    billing_config = False
    advisor_config = False


    for key, value in policies.items():
        
        if re.search(billing_policy_pat,key):
            if billing_policies.items() == value.items():
                billing_config = True
            else:
                print(f"The {billing_policy_name} isn't configured properly.")

        elif re.search(advisor_policy_pat,key):
            if advisor_policies.items() == value.items():
                advisor_config = True
            else:
                print(f"The {advisor_policy_name} isn't configured properly.")

    return {'billing_config': billing_config, 'advisor_config': advisor_config}


def verify_policy_permissions(policies: List[str]):
    """
        checks the permissions set for a list of policies against the LeanIX prescribed permissions.
        see https://dev.leanix.net/docs/cloud-intelligence#section-aws-user-setup 
    """

    iam = boto3.client('iam')
    policy_container = dict()
    for policy in policies:
        policy_version = iam.get_policy(PolicyArn=policy)[
            'Policy']['DefaultVersionId']
        permission = iam.get_policy_version(
            PolicyArn=policy,
            VersionId=policy_version)['PolicyVersion']['Document']

        policy_container[policy] = permission

    config_health = compare_with_leanix(policy_container)

    print(config_health)


@click.command()
@click.option('--username', '-u', 'username', required=True,
              help="AWS Username")
def cli(username):
    user_policies = authenticated_scan_policies(username=username)
    verify_policy_permissions(user_policies)
