import boto3
from haws.exceptions.authentication import UnauthenticatedUserCredentials
from haws.main import logger
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
import botocore
import os
from rich.console import Console
from typing import List


def get_tags():
    try:
        ce = boto3.client('ce')
        today = dt.today()
        backdate = today + relativedelta(months=-6)
        backdate = backdate.strftime('%Y-%m-%d')
        today = today.strftime('%Y-%m-%d')

        tags = ce.get_tags(
            SearchString='',
            TimePeriod={
                'Start': backdate,
                'End': today
            }
        )['Tags']

        logger.info(f'found {len(tags)} active cost allocation tag(s)', extra={
                    "markup": True})
        return tags
    except botocore.exceptions.ClientError as e:
        print(e)
        return None


def create_tag_report(tags: List[str]):
    num_healthchecks = 0
    cwd = os.getcwd()
    filename = cwd+'/report.txt'
    failed_checks = 0
    passed_checks = 0

    with open(filename, 'a') as fh:
        console = Console(file=fh, width=75)
        console.print('\n')
        console.rule("Active Cost Allocation Tags")

        for index, tag in enumerate(tags):
            index += 1
            console.print(f'{index}: [bold white] {tag} [/bold white] ')
    
    logger.info(f'saved cost allocation report {filename}', extra={
                    "markup": True})


def run_cost_tag_check():
    tags = get_tags()
    create_tag_report(tags=tags)
