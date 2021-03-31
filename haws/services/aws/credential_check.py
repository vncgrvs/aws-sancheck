import boto3
import botocore
import json
import re
import click
import os
from haws.main import logger
from os import path
import sys
from rich.prompt import Prompt
from haws.services.setup_helper import get_runtime_settings


def get_user_credentials():

    # click.prompt(text="Your AWS ID: ", type=str)
    id = Prompt.ask("[blue bold]Your AWS ID: [/blue bold]")
    # click.prompt(text="Your AWS Key: ", type=str, hide_input=True)
    key = Prompt.ask("[blue bold]Your AWS Key: [/blue bold]", password=True)

    return id, key


def verify_credentials(aws_access_key_id: str, aws_secret_access_key: str, extended: bool = False):
    pattern = re.compile('user/(.*)')
    sts = boto3.client('sts',
                       aws_access_key_id=aws_access_key_id,
                       aws_secret_access_key=aws_secret_access_key)

    try:
        res = sts.get_caller_identity()
        if (not os.getenv('AWS_ACCESS_KEY_ID')) or (not os.getenv('AWS_SECRET_ACCESS_KEY')):
            logger.info("[info]Credentials are valid[/info]",
                    extra={"markup": True})
            os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key_id
            os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_access_key
            
        if not extended:
            return True
        else:
            username = re.search(pattern, res['Arn']).group(1)
            out = {
                "check": True,
                "user_arn": res['Arn'],
                "account": res['Account'],
                "username": username
            }
            return out
    except botocore.exceptions.ClientError:
        if not extended:
            return False
            sys.exit()
        else:
            logger.error('[danger] Credentials invalid. Please check and re-run; [white]haws setup[/ white] [/danger]',
                         extra={"markup": True})
            sys.exit()

    except Exception as e:
        logger.exception(e, exc_info=True)
        if not extended:
            return False
            sys.exit()
        else:
            username = re.search(pattern, res['Arn']).group(1)
            out = {
                "check": False,
                "user_arn": res['Arn'],
                "account": res['Account'],
                "username": username
            }
            sys.exit()


def login():
    if not path.exists('haws/config/runtime.json'):
        logger.error('[danger]Please run [white] haws setup[/white] first', extra={
                     "markup": True})
        sys.exit()
    else:
        settings = get_runtime_settings()
        aws_id = settings['aws_id']
        aws_key = settings['aws_key']

    check = verify_credentials(
        aws_access_key_id=aws_id, aws_secret_access_key=aws_key, extended=True)

    return check
