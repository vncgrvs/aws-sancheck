import click
from haws.services.aws.policy_check import *

@click.command()
def cli():
    run_policy_check()