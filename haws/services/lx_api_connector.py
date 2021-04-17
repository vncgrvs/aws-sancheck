import json
import requests
import pandas as pd
from typing import List
from haws.services.setup_helper import get_runtime_settings
from haws.main import logger


# Get the bearer token - see https://dev.leanix.net/v4.0/docs/authentication

def authenticate():
    settings = get_runtime_settings()
    api_token = settings['lx_apitoken']
    lx_host = settings['lx_host']
    auth_url = f'https://{lx_host}.leanix.net/services/mtm/v1/oauth2/token'

    response = requests.post(auth_url, auth=('apitoken', api_token),
                             data={'grant_type': 'client_credentials'})

    try:
        response.raise_for_status()
        access_token = response.json()['access_token']
        bearer_token = 'Bearer ' + access_token
        logger.info(
            f'[bold green]Authenticated with LeanIX API Token[/]', extra={"markup": True})
    except requests.exceptions.HTTPError as err:
        logger.exception(err, exc_info=True)
        logger.error(f'Shutting down due to invalid LeanIX API credentials')

    return bearer_token


def overwrite_scan_config(scan_config: List[dict]):
    logger.info(f'[info]already writing discovered billing account[/info] {billing_ac} [info]to scan config...[/info]', extra={
            "markup": True})
    bearer_token = authenticate()
    settings = get_runtime_settings()
    lx_host = settings['lx_host']

    endpoint = f"https://{lx_host}.leanix.net/services/cloudockit-connector/v1/configurations/overwrite"
    header = {
        'Authorization': bearer_token,
        'Content-Type': 'application/json'
    }
    
    json_data = json.dumps(scan_config)

    response = requests.post(url=endpoint, headers=header, data=json_data)
    try:
        response.raise_for_status()
        if response.status_code == 200:
            logger.info(
                ':tada:[bold green] LeanIX Scan config successfully changed.[bold green]', extra={"markup": True})
    except requests.exceptions.HTTPError as err:
        logger.exception(err, exc_info=True)
