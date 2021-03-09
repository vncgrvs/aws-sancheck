import boto3
import json
import click
import os

def get_user_credentials():
    id = click.prompt(text="Your AWS ID: ", type=str)
    key = click.prompt(text="Your AWS Key: ", type=str, hide_input=True)

    return id,key

def verify_credentials(aws_access_key_id: str, aws_secret_access_key: str):
    sts = boto3.client('sts',
                       aws_access_key_id=aws_access_key_id,
                       aws_secret_access_key=aws_secret_access_key)

    try:
        sts.get_caller_identity()
        print("The AWS credentials are valid.")
        os.environ['AWS_ACCESS_KEY_ID']=aws_access_key_id
        os.environ['AWS_SECRET_ACCESS_KEY']=aws_secret_access_key
        return True
    except Exception as e:
        print(e)
        return False


@click.command()
@click.pass_context
def cli(ctx):
    
    id,key = get_user_credentials()
    credential_check = verify_credentials(aws_access_key_id=id, aws_secret_access_key=key)


    
        
        

        

