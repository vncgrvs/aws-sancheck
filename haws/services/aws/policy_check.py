import boto3
import botocore
import re
from rich.prompt import Confirm
import sys
import os
from os import path
from haws.services.setup_helper import setup_cli
from rich.console import Console
from typing import List
from haws.config.leanix_policies import leanix_policies
from haws.main import logger, runtime
from haws.services.aws.credential_check import login
from haws.exceptions.authentication import AccessDenied, UnauthenticatedUserCredentials, NoRuntimeSettings, InvalidUserCredentials


def check_user_policies(username: str):
    """
        gets all AWS policies attached to a user, fetched by his/her AWS username,
        and checks whether the LeanIX CI Policies were created.
        This check does not pick up policies via group assignment

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
        logger.info(
            f'[info]no policies assigned to user {username} directly[/info]', extra={"markup": True})

    else:

        logger.info(
            f'[info]policies assigned to user [white bold]{username}[/white bold] directly: {user_policies}[/info]', extra={"markup": True})

    if len(group_assigned_policies) == 0:

        logger.info(
            f'[info]no policies assigned via group adherence[/info]', extra={"markup": True})
    else:
        logger.info(
            f'[info]policies assigned via group: {group_assigned_policies}[/info]', extra={"markup": True})

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

    try:
        user_policies = get_all_user_policies(username=username)
    except botocore.exceptions.NoCredentialsError:
        logger.error(
            '[danger]User not authenticated.[/danger]', extra={"markup": True})
        user_policies = None
        raise UnauthenticatedUserCredentials("User is not authenticated")

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
                'req_permission': data['req_permissions'],
                'mandatory': data['mandatory']
            }
        else:
            if ('aws_permission' in data) and (data['req_permissions'] is not None):
                output[policy] = {
                    'exists': data['exists'],
                    'aws_permission': data['aws_permission'],
                    'req_permission': data['req_permissions'],
                    'permission_check': False,
                    'mandatory': data['mandatory']

                }
            else:
                output[policy] = {
                    'exists': data['exists'],
                    'aws_permission': None,
                    'req_permission': data['req_permissions'],
                    'permission_check': False,
                    'mandatory': data['mandatory']

                }

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
                'aws_permission': permission,
                'exists': data['exists'],
                'req_permissions': data['req_permissions'],
                'mandatory': data['mandatory']
            }
        else:
            policy_container[policy] = {
                'req_permissions': data['req_permissions'],
                'exists': data['exists'],
                'mandatory': data['mandatory']
            }

    return policy_container


def filter_policies(policies: List[str], leanix_policies: dict = leanix_policies) -> dict:
    """
        checks if policy names defined in leanix_policies.py are contained in AWS Scan User.
        #section-aws-user-setup for LeanIX requried policies.
        see https://dev.leanix.net/docs/cloud-intelligence
    """

    regex_collector = dict()
    filtered_policies = dict()
    unmatched_policies = list(leanix_policies.keys())

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
                    'exists': True,
                    'req_permissions': data['permissions'],
                    'mandatory': True
                }
                unmatched_policies.remove(policy)
        if count == 0:
            filtered_policies[policy] = {
                'exists': False, 'req_permissions': None, 'mandatory': False}

    if len(unmatched_policies) != 0:
        for missing_policy in unmatched_policies:
            filtered_policies[missing_policy] = {
                'exists': False, 'req_permissions': None, 'mandatory': True}

    # with open('permission.json', 'w', encoding='utf-8') as fh:
    #     json.dump(filtered_policies, fh, indent=4)

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

    return validated_permissions


def create_policy_report(policy_checks: dict):
    num_healthchecks = 0
    cwd = os.getcwd()
    filename = cwd+'/report.txt'
    failed_checks = 0
    passed_checks = 0

    with open(filename, 'w') as fh:
        console = Console(file=fh, width=75)
        console.rule("Policy Checks")

        for policy, data in policy_checks.items():
            if (data['exists'] and data['permission_check']
                    and data['mandatory']):
                console.print(
                    f':white_check_mark: {policy} is set up correctly')
                passed_checks += 1
                num_healthchecks += 1
            elif (data['exists'] and not data['permission_check']
                  and data['mandatory']):
                failed_checks += 1
                num_healthchecks += 1
                console.print(
                    f':stop_sign: {policy} does not comply with the naming convention or the wrong policy(-ies) was attached')
            elif (not data['exists'] and not data['permission_check'] and
                  not data['mandatory']):
                console.print(
                    f':information_source: {policy} was found but is not mandatory for the LeanIX Scan Agent')
            elif (not data['exists'] and data['mandatory']):
                failed_checks += 1
                num_healthchecks += 1
                console.print(
                    f':stop_sign: {policy} is not attached to the user, but is mandatory')
        console.rule()

        logger.info('[bold]AWS Policy Checks[/bold]', extra={"markup": True})
        if passed_checks == num_healthchecks:
            console.print(
                f'[bold]:white_check_mark: {passed_checks}/{num_healthchecks} checks passed[/bold]')
            logger.info(
                f'[bold]:white_check_mark: {passed_checks}/{num_healthchecks} checks passed[/bold]', extra={"markup": True})
        else:
            if passed_checks != 0:
                logger.info(
                    f'[bold]:white_check_mark: {passed_checks}/{num_healthchecks} checks passed[/bold]', extra={"markup": True})
            logger.warning(
                f'[bold red]:stop_sign: {failed_checks}/{num_healthchecks} checks failed[/bold red]. please see the details: [bold]{filename}[/bold]',
                extra={"markup": True})
            console.log(
                f'[bold red]:stop_sign: {failed_checks}/{num_healthchecks} checks failed[/bold red].')


def run_policy_check(save_runtime: bool):
    try:
        login_info = login()
        if login_info['check']:
            user_policies = authenticated_scan_policies(
                username=login_info['username'])
            policy_checks = verify_permissions(policies=user_policies)

        create_policy_report(policy_checks=policy_checks)

    except AccessDenied:
        sys.exit()

    except (UnauthenticatedUserCredentials, NoRuntimeSettings,
            InvalidUserCredentials):
        rerun = Confirm.ask("Do you want to setup the healthchecker? [y/n]")
        if rerun:
            setup_cli()
            login_info = login()
            if login_info['check']:
                user_policies = authenticated_scan_policies(
                    username=login_info['username'])
                policy_checks = verify_permissions(policies=user_policies)

            create_policy_report(policy_checks=policy_checks)
        else:
            if not save_runtime:
                if path.exists(runtime):
                    os.remove(runtime)
                    logger.info("[info]removed runtime.json [/info]",
                                extra={"markup": True})
            logger.info("[info]shutting down[/info]", extra={"markup": True})
            sys.exit()
