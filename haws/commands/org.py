from haws.services.aws.organization import *
from haws.commands.credentials import login

def run_org_check():
    pass


@click.command()
def cli():
    out = login()
    account_id = out['account']

    if is_billing_account(account_id=account_id):
        root_id = get_root()
        org_list = traverse_ous(root_id=root_id)
        get_accounts_for_org_chart(org=org_list)
