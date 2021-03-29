import click

@click.command()
@click.pass_context
def cli(ctx):
    print("run.py")

