from pathlib import Path
import json

root_dir = str(Path(__file__).parent.parent.absolute())
runtime = root_dir + '/config/runtime.json'


def get_runtime_settings(filename: str = runtime):

    with open(filename, 'r') as fh:
        settings = json.load(fh)

    return settings
