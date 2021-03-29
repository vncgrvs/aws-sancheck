import click
import os
import logging
import sys
import datetime
from rich.console import Console

plugin_folder = os.path.join(os.path.dirname(__file__), 'commands')
console = Console()


logger = logging.getLogger(__name__)
    
f_handler = logging.FileHandler('./services/healthcheck.log', mode='w+')
f_formatter = logging.Formatter('%(levelname)s-%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

f_handler.setFormatter(f_formatter)

logger.addHandler(f_handler)
logger.setLevel(logging.INFO)

    
    
class AWSScanner(click.MultiCommand):

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(plugin_folder):
            if filename.endswith('.py') and not filename.startswith('__'):
                rv.append(filename[:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        fn = os.path.join(plugin_folder, name + '.py')
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        return ns['cli']

# # cli = MyCLI(help='This tool\'s subcommands are loaded from a '
#             'plugin folder dynamically.')


@click.group(cls=AWSScanner, help='This tool runs preparatory sanity checks to enable the LeanIX scan agent')
@click.pass_context
def cli(ctx):
    logger.info('Initialized Logger')
    


if __name__ == '__main__':
    console.print(":tornado:[bold blue] LEANIX AWS HEALTHCHECK ")
    print(sys.path)
    cli()