import click
from haws.services.setup_helper import setup_cli


@click.command()
@click.pass_context
def cli(ctx):
    setup_cli()
