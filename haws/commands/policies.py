import boto3
import json
import botocore
import click
import sys
import re
from typing import List
from haws.commands.credentials import get_user_credentials, verify_credentials
from haws.services.leanix_policies import leanix_policies
from haws.main import logger


def check_user_policies(username: str):
    """
        gets all AWS policies attached to a user, fetched by his/her AWS username, and checks whether the LeanIX CI Policies
        were created. This check does not pick up policies via group assignment

    """

    iam = boto3.client('iam')
    pattern = re.compile(
        'LeanIXCloudScanAdvisorPolicyReader|LeanIXCloudScanBillingPolicyReader|arn:aws:iam::aws:policy/ReadOnlyAccess')
    policies = iam.list_attached_user_policies(UserName=username)
    user_policies = list()

    for policy in policies['AttachedPolicies']:
        policy_arn = policy['PolicyArn']
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

    if len(user_policies) == 0:
        logger.info(f'No Policies assigned to User {username} directly')

    else:

        logger.info(
            f'Policies assigned to User {username} directly: {user_policies}')

    if len(group_assigned_policies) == 0:

        logger.info(f'No Policies assigned via Group adherence')
    else:
        logger.info(f'Policies assigned via Group: {group_assigned_policies}')

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
        logger.info('User successfully authenticated.')
    except botocore.exceptions.NoCredentialsError:
        logger.error('User not authenticated.')
        print("Seems like you're not authenticated. Let's try to authenticate...")
        id, key = get_user_credentials()
        credential_check = verify_credentials(
            aws_access_key_id=id, aws_secret_access_key=key)

        if credential_check:
            user_policies = get_all_user_policies(username=username)

        else:
            print("Authentication failed! Please check credentials")
            logger.error('User failed to authenticate in second attempt.')
            sys.exit()
            user_policies = None

    return user_policies


def compare_with_leanix(policies: dict):
    """
        compares specified policy permssions with LeanIX's prescribed policy permission set under
        requirements.py
    """

    output = dict()
    for policy, data in policies.items():

        if data['exists']:
            permission_check = data['req_permissions'].items(
            ) == data['aws_permission'].items()
            output[policy] = {
                'exists': data['exists'],
                'permission_check': permission_check,
                'aws_permission': data['aws_permission'],
                'req_permission': data['req_permissions']
            }
        else:
            output[policy] = {
                'exists': data['exists'],
                'aws_permission': data['aws_permission'],
                'req_permission': data['req_permissions']

            }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    return output


def get_policy_permissions(policies: dict):
    """
        retrieves the permissions set for a list of policies.
    """

    iam = boto3.client('iam')
    policy_container = dict()
    for policy, data in policies.items():
        if data['exists']:
            policy_version = iam.get_policy(PolicyArn=policy)[
                'Policy']['DefaultVersionId']
            permission = iam.get_policy_version(
                PolicyArn=policy,
                VersionId=policy_version)['PolicyVersion']['Document']

            policy_container[policy] = {
                'aws_permission': permission, 'exists': data['exists'], 'req_permissions': data['req_permissions']}
        else:
            policy_container[policy] = {
                'req_permission': data['req_permissions'], 'exists': existence}

    return policy_container


def filter_policies(policies: List[str], leanix_policies: dict = leanix_policies) -> dict:
    """
        checks if policy names defined in leanix_policies.py are contained in AWS Scan User. 
        see https://dev.leanix.net/docs/cloud-intelligence#section-aws-user-setup for LeanIX requried policies.
    """

    regex_collector = dict()
    filtered_policies = dict()

    for policy_name, permissions in leanix_policies.items():
        string_match = re.compile(policy_name)
        regex_collector[policy_name] = {
            'regex': string_match, 'permissions': permissions}

    for policy in policies:

        count = 0
        for policy_arn, data in regex_collector.items():
            if re.search(data['regex'], policy):
                count += 1
                filtered_policies[policy] = {
                    'exists': True, 'req_permissions': data['permissions']}
        if count == 0:
            filtered_policies[policy] = {
                'exists': False, 'req_permissions': None}

    return filtered_policies


def verify_permissions(policies: List[str]) -> dict:
    """
        processes a set of policies and checks their containing permissions against the required LeanIX permissions stipulated 
        under leanix_policies.py. 

        :param policies list
        :returns dict:
        {
            "policy": {
                "exists": Bool - whether LeanIX policy exists in User policies
                "permission_check": Bool - True if permissions match LeanIX permissions; False if not
                "req_permission": required permissions; returned if permission check fails
            }
        }

    """

    filtered_policies = filter_policies(policies=policies)
    permissions = get_policy_permissions(filtered_policies)
    validated_permissions = compare_with_leanix(permissions)

    logger.info(f'Policy Verifcation Outcome: {validated_permissions}')
    return validated_permissions

def run_policy_check(username: str):
    user_policies = authenticated_scan_policies(username=username)
    policy_checks = verify_permissions(policies=user_policies)

    num_healthchecks = len(policy_checks.keys())
    failed_checks = 0
    passed_checks = 0
    print('-----------  POLICY CHECK SUMMARY  -------------')
    for policy , data in policy_checks.items():
        if (data['exists'] and data['permission_check']):
            print(f'{policy} is correctly set up')
            passed_checks +=1
        else:
            failed_checks += 1
            if not data['exists']:
                print(f'{policy} does not comply with the naming convention or the wrong policy was attached')
            if not data['permission_check']:
                print(f'{policy}s permissions do not comply with LeanIX specified permissions')
    print('-----------------')

    if passed_checks == num_healthchecks:
        print(f'{passed_checks}/{num_healthchecks} checks passed')
    else:
        print(f'{failed_checks}/{num_healthchecks} checks failed')


@click.command()
@click.option('--username', '-u', 'username', required=True,
              help="AWS Username")
def cli(username):
    user_policies = authenticated_scan_policies(username=username)
    policy_checks = verify_permissions(policies=user_policies)

    num_healthchecks = len(policy_checks.keys())
    failed_checks = 0
    passed_checks = 0
    print('-----------  POLICY CHECK SUMMARY  -------------')
    for policy , data in policy_checks.items():
        if (data['exists'] and data['permission_check']):
            print(f'{policy} is correctly set up')
            passed_checks +=1
        else:
            failed_checks += 1
            if not data['exists']:
                print(f'{policy} does not comply with the naming convention or the wrong policy was attached')
            if not data['permission_check']:
                print(f'{policy}s permissions do not comply with LeanIX specified permissions')
    print('-----------------')

    if passed_checks == num_healthchecks:
        print(f'{passed_checks}/{num_healthchecks} checks passed')
    else:
        print(f'{failed_checks}/{num_healthchecks} checks failed')

        

