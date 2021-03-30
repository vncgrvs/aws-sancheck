import json
import requests
import pandas as pd
from haws.services.auth import LX_API_TOKEN, LX_HOST
from haws.main import logger


api_token = LX_API_TOKEN
auth_url = f'https://{LX_HOST}.leanix.net/services/mtm/v1/oauth2/token'


# Get the bearer token - see https://dev.leanix.net/v4.0/docs/authentication

def authenticate(api_token: str = api_token, auth_url: str = auth_url):
    response = requests.post(auth_url, auth=('apitoken', api_token),
                             data={'grant_type': 'client_credentials'})

    try:
        response.raise_for_status()
        access_token = response.json()['access_token']
        bearer_token = 'Bearer ' + access_token
        logger.info(
            f'[bold green] Authenticated with LeanIX API Token[/]', extra={"markup": True})
    except requests.exceptions.HTTPError as err:
        logger.exception(err, exc_info=True)
        logger.error(f'Shutting down due to invalid LeanIX API credentials')

    return bearer_token


def overwrite_scan_config():
    bearer_token = authenticate()
    header = {
        'Authorization': f'Bearer {bearer_token}',
        'Content-Type': 'application/json'
    }

    with open('scan_config.json', 'r+', encoding='utf-8') as f:
        data = json.load(f)

    response = requests.post(url=request_url, headers=header, data=json_data)
    try:
        response.raise_for_status()
        if response.status_code == 200:
            logger.info('[info]LeanIX Scan config successfully changed.[/info]')
    except requests.exceptions.HTTPError as err:
        logger.exception(err,exc_info=True)


    


if __name__ == "__main__":
    authenticate()
