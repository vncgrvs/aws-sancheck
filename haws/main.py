import click
import os
import io
import logging
import sys
import datetime
from rich.console import Console
from rich.padding import Padding
from rich.logging import RichHandler
from rich.theme import Theme
from pathlib import Path

root_dir = str(Path(__file__).parent.absolute())
runtime = root_dir + '/config/runtime.json'

plugin_folder = os.path.join(os.path.dirname(__file__), 'commands')
logger_config = os.path.dirname(__file__) + '/config/logger.ini'
health_log = os.path.dirname(__file__) + '/services/healthcheck.log'

logger_console = Console(theme=Theme().read(
    logger_config), log_time_format='%b-%d-%y %H:%M:%S')
logger = logging.getLogger(__name__)
f_handler = logging.FileHandler(health_log, mode='w+')
f_formatter = logging.Formatter(
    '%(levelname)s-%(asctime)s - %(message)s - line %(lineno)d - %(filename)s', datefmt='%b-%d-%y %H:%M:%S')

f_handler.setFormatter(f_formatter)

logger.addHandler(f_handler)
logger.addHandler(RichHandler(console=logger_console, rich_tracebacks=True))
logger.setLevel(logging.INFO)


class AWSScanner(click.MultiCommand):

    def list_commands(self, ctx):
        rv = ['setup', 'run']
        # for filename in os.listdir(plugin_folder):
        #     if filename.endswith('.py') and not filename.startswith('__'):
        #         rv.append(filename[:-3])
        # rv.sort()
        return rv

    def get_command(self, ctx, name):
        ns = {}
        fn = os.path.join(plugin_folder, name + '.py')
        with open(fn) as f:
            code = compile(f.read(), fn, 'exec')
            eval(code, ns, ns)
        return ns['cli']

    def format_help(self, ctx, formatter):
        sio = io.StringIO()
        console = Console(file=sio, force_terminal=True)
        console.print(
            ":tornado: [bold blue] LEANIX AWS HEALTHCHECKER", justify="center")
        # console.print("\n")
        console.print(
            "[bold]Description[/bold]: [italic]A Python CLI to sanity check the AWS scanning config", justify="center")
        console.print(
            "[bold]Support[/bold]:[italic]support@leanix.net", justify="center")
        console.print("[bold magenta] Commands",)
        for cmd in self.list_commands(ctx):
            console.print(f"[bold blue]{cmd} [/bold blue] ")
        formatter.write(sio.getvalue())


@click.group(cls=AWSScanner)
@click.pass_context
def cli(ctx):
    pass


if __name__ == '__main__':
    cli()
