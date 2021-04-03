import click
from haws.services.aws.policy_check import *
from haws.services.aws.organization_check import *
from haws.exceptions.authentication import *
from haws.services.setup_helper import setup_cli
from rich.prompt import Confirm
import sys
from pathlib import Path
import os
from os import path
from haws.main import logger, runtime


@click.command()
def cli():
    print(runtime)
    try:
        run_policy_check()
        run_org_check()
    except (UnauthenticatedUserCredentials, NoRuntimeSettings, InvalidUserCredentials):
        rerun = Confirm.ask("Do you want to run the setup? [y/n]")
        if rerun:
            setup_cli()
        else:
            if path.exists(runtime):
                os.remove(runtime)
                logger.info("[info]removed runtime.json [/info]",
                            extra={"markup": True})
            logger.info("[info]shutting down[/info]", extra={"markup": True})
            sys.exit()
    except (MultipleRoots, GeneralAuthError):
        if path.exists(runtime):
            os.remove(runtime)
            logger.info("[info] removed runtime.json [/info]",
                        extra={"markup": True})
        logger.info("[info]shutting down[/info]", extra={"markup": True})
        sys.exit()
