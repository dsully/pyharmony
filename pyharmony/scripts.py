"""Command line utility for querying Logitech Harmony devices."""

import asyncio
import configparser
import json
import logging
import os
import sys

import click
import click_log

from .auth import SessionTokenClient
from .client import HarmonyClient

log = logging.getLogger(__name__)


@click.group()
@click.option('--hostname', help='Hostname or IP Address of the Harmony device.')
@click.option('--port', default=5222, type=int, help='Network port that the Harmony is listening on.')
@click_log.simple_verbosity_option()
@click_log.init(__name__)
@click.pass_context
def cli(ctx, hostname, port):

    parser = configparser.ConfigParser()
    parser.read(os.path.expanduser('~/.pyharmony.ini'))

    try:
      config = parser['harmony']
    except KeyError:
      config = parser['DEFAULT']

    ctx.obj = {
        'hostname': config.get('hostname', hostname),
        'port': config.get('port', port),
    }


@cli.command()
@click.option('--filename', type=click.Path(), default='-', help='Filename to write the config out to. Default is STDOUT')
@click.pass_context
def show_config(ctx, filename):
    """Connects to the Harmony and prints its configuration."""

    token = SessionTokenClient.login(**ctx.obj)
    client = HarmonyClient(ctx.obj['hostname'], ctx.obj['port'], token)

    tasks = asyncio.gather(*[client.get_config()])
    client.loop.run_until_complete(tasks)
    client.disconnect()

    config = json.dumps(next(iter(tasks.result())), indent=2)

    with click.open_file(filename, 'w') as fh:
      fh.write(config)

    sys.exit(0)
