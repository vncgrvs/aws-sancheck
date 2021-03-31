import boto3
import json
import pandas as pd
import botocore
from typing import List
import click
import numpy as np
from haws.main import logger
from haws.services.aws.credential_check import login
from haws.services.lx_api_connector import overwrite_scan_config
import sys
import os


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
        # logger.info(f'Billing Account: {out}')
    else:
        logger.info(
            f'{account_id} is not billing account! \n Please ensure Scan Agent is created with account id: {billing_ac}')
        out = {
            "is_billing_account": False,
            "billing_ac": billing_ac,
            "scan_agent_account_id": account_id
        }
        logger.info(f'Billing Account: {out}')

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
    root = org.list_roots()['Roots']
    root_id = None

    if len(root) > 1:
        logger.error(f'Found {len(root)} roots. Can only handle one root.')
        sys.exit()

    elif len(root) == 1:
        root_id = root[0]['Id']

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

    total = pd.merge(org, account_map, how='left', left_on='child_id', right_on='parent_id')
    cwd = os.getcwd()
    file_path = cwd+'/entire_org.pkl'
    total.to_pickle(file_path)
    logger.info(f'saved traversed org chart @ {file_path}.//[grey italic] use [bold]pandas[/bold] to open [/grey italic]', extra={"markup": True})
    return total


def get_relevant_accounts(org_df: pd.DataFrame):
    filter_words = 'sandbox|prod|test|^qa$|root'
    org_clean = org_df[org_df.account_id.notnull()].copy()
    org_clean = org_clean[org_clean.account_name.str.contains(
        pat=filter_words, case=False)]
    collector = list()

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
        overwrite_scan_config(scan_config=payload)
