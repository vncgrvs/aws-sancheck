import click
from haws.services.aws.organization_check import run_org_check
from haws.commands.credentials import login


@click.command()
def cli():
    run_org_check()