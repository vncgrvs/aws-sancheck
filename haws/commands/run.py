import click
from haws.services.aws.policy_check import *
from haws.services.aws.organization_check import *

@click.command()
def cli():
    
    run_policy_check()
    run_org_check()