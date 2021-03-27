import boto3
import json
import botocore
from typing import List
import click
from main import logger
import sys
from commands.credentials import login
from auth import AWS_ID, AWS_KEY
import os
from exceptions.org_exceptions import NoOUsFound


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


def get_parents(parents: List[str]):
    org = boto3.client('organizations')
    org_chart = dict()

    for parent in parents:
        collector = list()
        ous = org.list_organizational_units_for_parent(
            ParentId=parent)['OrganizationalUnits']

        if len(ous) != 0:  # only if children exist
            for child in ous:
                collector.append(child['Id'])
            org_chart[parent] = collector

    return org_chart


def traverse_ous(root_id: str):

    org_chart = list()

    circuit_breaker = False
    level = 1
    parent = [root_id]
    
    while not circuit_breaker:
        """
            1. for all parents get children
            2. get children for parents with children
            3. continue until all selected parents dont have any children
        """
        if parent == [root_id]:
            new_children = get_parents(parents=parent)
            parent = new_children
            
        else:
            keys = list(parent.keys())
            col = list()
            super_parent = parent
            no_child_counter = 0
            for key in keys:
                parent = get_parents(super_parent[key])
                if len(parent) == 0:
                    no_child_counter += 1
                
            
            if no_child_counter == len(keys):
                circuit_breaker = True

        if len(parent)!=0:
            org_chart.append(parent)


    return org_chart
    # with open('org.json', 'w') as f:
    #     json.dump(org_chart, f, indent=4)


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

def build_org_json(org_list:List):
    base = org_list[0]

    for part in org_list[1:]:
        print(part)

    

def run_org_check():
    pass


@click.command()
def cli():
    out = login()
    account_id = out['account']

    if is_billing_account(account_id=account_id):
        root_id = get_root()
        org_list=traverse_ous(root_id=root_id)
        build_org_json(org_list=org_list)
        
        
       