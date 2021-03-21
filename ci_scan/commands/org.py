import boto3
import json
import botocore
import click
from main import logger
import sys
from commands.credentials import login
from auth import AWS_ID, AWS_KEY
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
        print(f'Account {account_id} is billing account')

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


def get_ous(root_id: str):
    org = boto3.client('organizations')

    ous = org.list_organizational_units_for_parent(
        ParentId=root_id)['OrganizationalUnits']

    collector = list()

    for ou in ous:
        ou_id = ou['Id']
        ou_arn = ou['Arn']
        ou_name = ou['Name']

        ou_tmp = {
            'id': ou_id,
            'arn': ou_arn,
            'name': ou_name
        }

        collector.append(ou_tmp)

    return collector


def get_root():
    org = boto3.client('organizations')
    root = org.list_roots()['Roots']
    root_id = None

    if len(root) > 1:
        logger.error(f'Found {len(root)}. Can only handle one root.')
        sys.exit()

    elif len(root) == 1:
        root_id = root[0]['Id']

    return root_id


def run_org_check():
    pass


@click.command()
def cli():
    out = login()
    account_id = out['account']

    if is_billing_account(account_id=account_id):
        root_id = get_root()

        print(get_ous(root_id=root_id))
