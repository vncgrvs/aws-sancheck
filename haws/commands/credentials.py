import click
from haws.services.aws.credential_check import *

@click.command()
@click.pass_context
def cli(ctx):

    id, key = get_user_credentials()
    credential_check = verify_credentials(
        aws_access_key_id=id, aws_secret_access_key=key)
