import json
import re
from rich.prompt import Prompt

def get_runtime_settings(filename:str = "haws/config/runtime.json"):

    with open(filename,'r') as fh:
        settings = json.load(fh)

    return settings

def setup_cli():
    aws_id = Prompt.ask("[blue bold]Your AWS ID: [/blue bold]")
    aws_key = key = Prompt.ask(
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

    with open('haws/config/runtime.json', 'w') as fh:
        json.dump(export, fh, indent=4)
