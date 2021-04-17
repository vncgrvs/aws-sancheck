import click
from haws.services.aws.cost_allocation_tags import *


@click.command()
@click.pass_context
def cli(ctx):
    setup_cli()

