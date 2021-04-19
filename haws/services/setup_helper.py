import json
import re
from rich.prompt import Prompt
from pathlib import Path
from haws.services.aws.credential_check import login

root_dir = str(Path(__file__).parent.parent.absolute())
runtime = root_dir + '/config/runtime.json'


def get_runtime_settings(filename: str = runtime):

    with open(filename, 'r') as fh:
        settings = json.load(fh)

    return settings


def update_runtime_settings(data: dict, filename: str = runtime):
    current_settings = get_runtime_settings(filename=filename)

    for key, value in data.items():
        current_settings[key] = value

    with open(runtime, 'w') as fh:
        json.dump(current_settings, fh, indent=4)


def setup_cli():
    aws_id = Prompt.ask("[blue bold]Your AWS ID: [/blue bold]")
    aws_key = Prompt.ask(
        "[blue bold]Your AWS Key: [/blue bold]", password=True)
    lx_apitoken = Prompt.ask("[blue bold]Your LeanIX API Token: [/blue bold]")
    lx_host = Prompt.ask("[blue bold]Your workspace url: [/blue bold]")

    pattern = re.compile(r'https://(.*).leanix')
    lx_host = re.search(pattern, lx_host).group(1)

    export = {
        'aws_id': aws_id,
        'aws_key': aws_key,
        'lx_host': lx_host,
        'lx_apitoken': lx_apitoken
    }

    with open(runtime, 'w') as fh:
        json.dump(export, fh, indent=4)
