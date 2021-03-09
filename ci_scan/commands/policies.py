import boto3
import botocore
import click
from commands.credentials import get_user_credentials, verify_credentials


def get_user_policies(username):
    iam = boto3.client('iam')
    policies = iam.list_attached_user_policies(UserName=username)
    user_policies = list()
    print(f"The user {username} has the following policies attached:")
    for policy in policies['AttachedPolicies']:
        user_policies.append(policy['PolicyArn'])
        print(policy['PolicyArn'])
    return user_policies


def verify_scan_policies(username: str):
    # assumes that roles are attached directly to user not via group assignment
    try:
        user_policies = get_user_policies(username=username)
    except botocore.exceptions.NoCredentialsError:
        print("Seems like you're not authenticated. Let's try to authenticate...")
        id, key = get_user_credentials()
        credential_check = verify_credentials(
            aws_access_key_id=id, aws_secret_access_key=key)

        if credential_check:
            user_policies = get_user_policies(username=username)

        else:
            print("Authentication failed! Please check credentials")


@click.command()
@click.option('--username', '-u', 'username', required=True,
              help="AWS Username")
def cli(username):
    verify_scan_policies(username=username)
