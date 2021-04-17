import boto3
import json
import pandas as pd
import botocore
from typing import List
import click
import numpy as np
from haws.main import logger
from haws.exceptions.authentication import AccessDenied
from haws.services.aws.credential_check import login
from haws.services.lx_api_connector import overwrite_scan_config
from haws.exceptions.authentication import MultipleRoots
from haws.services.setup_helper import update_runtime_settings
from haws.exceptions.billing import *
import os
from haws.services.setup_helper import get_runtime_settings


def get_org_details() -> dict:
    org = boto3.client('organizations')

    org_details = org.describe_organization()['Organization']

    billing_ac = org_details['MasterAccountId']
    billing_ac_arn = org_details['MasterAccountArn']

    org_info = {
        'billing_ac': billing_ac,
        'billing_ac_arn': billing_ac_arn
    }

    return org_info


def is_billing_account(account_id: str):
    org_info = get_org_details()
    billing_ac = org_info['billing_ac']

    if billing_ac == account_id:
        logger.info(f'Account {account_id} is the billing account')

        out = {
            "is_billing_account": True,
            "billing_ac": billing_ac,
            "scan_agent_account_id": account_id
        }

        update_runtime_settings({"billing_account_id": billing_ac})

    else:
        logger.warning(
            f'{account_id} [danger]is not billing account[/danger]', extra={
                "markup": True})
        logger.info(f'{billing_ac} is the billing account')
        out = {
            "is_billing_account": False,
            "billing_ac": billing_ac,
            "scan_agent_account_id": account_id
        }
        payload = [
            {
                "id": 'aws.'+str(billing_ac),
                "name": 'aws.billingaccount',
                "type": "aws",
                "data": {
                    "AWSAccessKeyId": "<AWSKEY>",
                    "AWSSecretAccessKey": "",
                    "SubscriptionID": billing_ac
                },
                "active": True
            }
        ]
        logger.error(f"[danger]the used IAM role doesnt have sufficient permissions to access information about the AWS organization structure.\n To allow the full functioning of this scirpt please create IAM role from:[/danger] {billing_ac}", extra={
                     "markup": True})
        
        

        

    return out


def get_parents(parents: List[str], df: pd.DataFrame):
    org = boto3.client('organizations')
    org_chart = dict()

    for parent in parents:
        collector = list()
        ous = org.list_organizational_units_for_parent(
            ParentId=parent)['OrganizationalUnits']

        if len(ous) != 0:  # only if children exist
            for child in ous:
                ou_name = child['Name']
                ou_id = child['Id']
                ou_arn = child['Arn']

                package = {
                    'parent_id': parent,
                    'child_id': ou_id,
                    'child_name': ou_name,
                    'child_arn': ou_arn
                }
                df = df.append(package, ignore_index=True)
                collector.append(ou_id)

            org_chart[parent] = collector

    return df, org_chart


def traverse_ous(root_id: str):

    org_chart = list()
    data = pd.DataFrame(
        columns=['parent_id', 'child_id', 'child_name', 'child_arn'])
    circuit_breaker = False
    parent = [root_id]

    while not circuit_breaker:
        """
            1. for all parents get children
            2. get children for parents with children
            3. continue until all selected parents dont have any children
        """
        if parent == [root_id]:
            package = {
                'parent_id': root_id,
                'child_id': root_id,
                'child_name': "root",
                'child_arn': np.nan
            }
            data = data.append(package, ignore_index=True)
            data, new_children = get_parents(parents=parent, df=data)
            parent = new_children

        else:
            keys = list(parent.keys())
            col = list()
            super_parent = parent
            no_child_counter = 0
            for key in keys:
                data, parent = get_parents(super_parent[key], data)

                if len(parent) == 0:
                    no_child_counter += 1

            if no_child_counter == len(keys):
                circuit_breaker = True

        if len(parent) != 0:
            org_chart.append(parent)
    cwd = os.getcwd()
    file_path = cwd+'/ou_chart.pkl'
    data.to_pickle(file_path)

    return data


def get_root():
    org = boto3.client('organizations')
    try:
        root = org.list_roots()['Roots']
        root_id = None

        if len(root) > 1:
            logger.error(f'Found {len(root)} roots. Can only handle one root.')
            raise MultipleRoots(
                'found multiple roots. Can only handle one root')

        elif len(root) == 1:
            root_id = root[0]['Id']

            
    except org.exceptions.AccessDeniedException:
        logger.warning("[danger]user doesnt have sufficient permissions to access roots", extra={
                       "markup": True})
        raise AccessDenied('User doesnt have the sufficient permissions')

    return root_id


def get_accounts_for_org_chart(org: pd.DataFrame):
    org_client = boto3.client('organizations')
    parents = list(org['child_id'].unique())
    account_map = pd.DataFrame(
        columns=['parent_id', 'account_id', 'account_arn', 'account_email', 'account_name'])

    for parent in parents:
        res = org_client.list_accounts_for_parent(ParentId=parent)['Accounts']
        if len(res) != 0:
            for account in res:

                if account['Status'] == "ACTIVE":
                    account_id = account['Id']
                    account_arn = account['Arn']
                    account_email = account['Email']
                    account_name = account['Name']

                    package = {
                        'parent_id': parent,
                        'account_id': account_id,
                        'account_arn': account_arn,
                        'account_email': account_email,
                        'account_name': account_name

                    }

                    account_map = account_map.append(
                        package, ignore_index=True)

    total = pd.merge(org, account_map, how='left',
                     left_on='child_id', right_on='parent_id')
    cwd = os.getcwd()
    file_path = cwd+'/entire_org.pkl'
    total.to_pickle(file_path)
    logger.info(
        f'saved traversed org chart @ {file_path}. //[grey italic] use [bold]pandas[/bold] to open [/grey italic]', extra={"markup": True})
    return total


def get_relevant_accounts(org_df: pd.DataFrame):
    filter_words = 'sandbox|prod|test|^qa$|root'
    org_clean = org_df[org_df.account_id.notnull()].copy()
    org_clean = org_clean[org_clean.account_name.str.contains(
        pat=filter_words, case=False)]
    collector = list()

    # already add billing account
    billing_account_id = get_runtime_settings()['billing_account_id']
    billing_account = {
        "id": 'aws.'+str(billing_account_id),
        "name": 'aws.billingaccount',
        "type": "aws",
        "data": {
                "AWSAccessKeyId": "<AWSKEY>",
            "AWSSecretAccessKey": "",
            "SubscriptionID": billing_account_id
        },
        "active": True
    }
    collector.append(billing_account)

    for index, row in org_clean.iterrows():
        account = {
            "id": 'aws.'+str(row['account_id']),
            "name": 'aws.'+str(row['account_name']).lower()+str(index),
            "type": "aws",
            "data": {
                "AWSAccessKeyId": "<AWSKEY>",
                    "AWSSecretAccessKey": "",
                    "SubscriptionID": row['account_id']
            },
            "active": True
        }

        collector.append(account)

    return collector


def run_org_check():
    login_info = login()
    account_id = login_info['account']

    if is_billing_account(account_id=account_id):
        root_id = get_root()
        org_list = traverse_ous(root_id=root_id)
        org_df = get_accounts_for_org_chart(org=org_list)
        payload = get_relevant_accounts(org_df=org_df)
        return payload
        
    else:
        raise BillingAccountInavailable(
            "IAM role not created within billing account")
        logger.warning(
            "[danger]No billing account found[/danger]", extra={"markup": True})
        return None
