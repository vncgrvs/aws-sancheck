import boto3
import json
import click
import os
from haws.main import logger
from os import path
import sys


def get_user_credentials():
    
    id = click.prompt(text="Your AWS ID: ", type=str)
    key = click.prompt(text="Your AWS Key: ", type=str, hide_input=True)

    return id, key


def verify_credentials(aws_access_key_id: str, aws_secret_access_key: str, extended: bool = False):
    sts = boto3.client('sts',
                       aws_access_key_id=aws_access_key_id,
                       aws_secret_access_key=aws_secret_access_key)

    try:
        res = sts.get_caller_identity()
        print("Credentials are valid")
        logger.info(f"Credentials are valid")
        os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key_id
        os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_access_key
        if not extended:
            return True
        else:
            out = {
                "check": True,
                "user_arn": res['Arn'],
                "account": res['Account']
            }
            return out
    except Exception as e:
        logger.exception(e, exc_info=True)
        if not extended:
            return False
            sys.exit()
        else:
            out = {
                "check": False,
                "user_arn": res['Arn'],
                "account": res['Account']
            }
            sys.exit()
            

def login():
    if not path.exists('auth.py'):
        id, key = get_user_credentials()
    else:
        from services.auth import AWS_ID, AWS_KEY
        id = AWS_ID
        key = AWS_KEY

    check = verify_credentials(aws_access_key_id=id, aws_secret_access_key=key,extended= True)

    return check


@click.command()
@click.pass_context
def cli(ctx):

    id, key = get_user_credentials()
    credential_check = verify_credentials(
        aws_access_key_id=id, aws_secret_access_key=key)
