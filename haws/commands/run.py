import click
from haws.services.aws.policy_check import *
from haws.services.aws.organization_check import *
from haws.services.aws.cost_allocation_tags import *
from haws.exceptions.authentication import *
from haws.services.setup_helper import setup_cli
from rich.prompt import Confirm
import sys
from pathlib import Path
import os
from os import path
from haws.main import logger, runtime
from haws.services.lx_api_connector import overwrite_scan_config


@click.command()
@click.option('--save-runtime', is_flag=True, default=False, help="whether to save credentials entered after run")
@click.option('--write-config', is_flag=True, default=False, help="whether to overwrite the scan config to the workspace")
def cli(save_runtime, write_config):
    try:
        run_policy_check()
        payload = run_org_check()
        
        
    except AccessDenied:
        pass
    
    except (UnauthenticatedUserCredentials, NoRuntimeSettings, InvalidUserCredentials):
        rerun = Confirm.ask("Do you want to setup the healthchcker? [y/n]")
        if rerun:
            setup_cli()
        else:
            if not save_runtime:
                if path.exists(runtime):
                    os.remove(runtime)
                    logger.info("[info]removed runtime.json [/info]",
                                extra={"markup": True})
            logger.info("[info]shutting down[/info]", extra={"markup": True})
            sys.exit()    
    finally:
        run_cost_tag_check()

        if write_config:
            overwrite_scan_config(scan_config=payload)

        if not save_runtime:
            if path.exists(runtime):
                os.remove(runtime)
                logger.info("[info]removed runtime config [/info]",
                            extra={"markup": True})
        