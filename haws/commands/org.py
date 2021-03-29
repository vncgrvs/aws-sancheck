import boto3
import json
import pandas as pd
import botocore
from typing import List
import click
from haws.main import logger
import sys
from haws.commands.credentials import login
from haws.services.auth import AWS_ID, AWS_KEY
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
        print(f'Account {account_id} is the billing account')

        out = {
            "is_billing_account": True,
            "billing_ac": billing_ac,
            "scan_agent_account_id": account_id
        }
        logger.info(out)
    else:
        print(f'{account_id} is not billing account! \n Please ensure Scan Agent is created with under account id: {billing_ac}')
        out = {
            "is_billing_account": False,
            "billing_ac": billing_ac,
            "scan_agent_account_id": account_id
        }
        logger.info(out)

    return out


def get_ous(parent_id: List[str]):
    org = boto3.client('organizations')

    ous = org.list_organizational_units_for_parent(
        ParentId=parent_id)['OrganizationalUnits']

    collector = dict()
    if len(ous) > 0:

        for ou in ous:
            ou_id = ou['Id']
            ou_arn = ou['Arn']
            ou_name = ou['Name']

            ou_tmp = {
                'arn': ou_arn,
                'name': ou_name
            }

            collector[ou_id] = ou_tmp
    elif len(ous) == 0:
        print(f'{parent_id} doesnt have any child-OUs')
        raise NoOUsFound

    return collector


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
    file_path = 'data_output/ou_chart.pkl'
    data.to_pickle(file_path)
    logger.info(f'saved traversed org chart @ {file_path}')
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
    parents = list(org['parent_id'].unique())
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
                   

    
    total = pd.merge(org,account_map,how='left',on='parent_id')
    file_path = 'data_output/entire_org.pkl'
    total.to_pickle(file_path)

def run_org_check():
    pass


@click.command()
def cli():
    out = login()
    account_id = out['account']

    if is_billing_account(account_id=account_id):
        root_id = get_root()
        org_list = traverse_ous(root_id=root_id)
        get_accounts_for_org_chart(org=org_list)
