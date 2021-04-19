import click
import os
from os import path
from haws.main import logger, runtime
from haws.services.lx_api_connector import overwrite_scan_config
from haws.services.aws.policy_check import run_policy_check
from haws.services.aws.organization_check import run_org_check
from haws.services.aws.cost_allocation_tags import run_cost_tag_check


@click.command()
@click.option('--save-runtime', is_flag=True, default=False,
              help="whether to save credentials entered after run")
@click.option('--write-config', is_flag=True, default=False,
              help="whether to overwrite the scan config to the workspace")
@click.option('--get-org', is_flag=True, default=False,
              help="whether to pull the AWS organization")
def cli(save_runtime, write_config, get_org):
    run_policy_check(save_runtime=save_runtime)
    run_cost_tag_check()

    if get_org:
        payload = run_org_check()

    if write_config and get_org:
        overwrite_scan_config(scan_config=payload)

    if not save_runtime:
        if path.exists(runtime):
            os.remove(runtime)
            logger.info("[info]removed runtime config [/info]",
                        extra={"markup": True})
