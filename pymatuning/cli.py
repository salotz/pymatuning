#!/usr/bin/env python
import sys

import click

from pymatuning.listings import *
from pymatuning.renderers.orgmode import listing

@click.command()
@click.option('--marker', type=click.Choice(['outline', 'checklist']), default="outline")
@click.argument('modname')
def orgmode(marker, modname):

    package = import_module(modname)

    i_tree = interface_tree(package)

    if marker == 'outline':
        m = '-'
    elif marker == "checklist":
        m = '- [ ]'

    org_listing = listing(i_tree, marker=m)

    click.echo(org_listing)



@click.group()
def cli():
    pass

cli.add_command(orgmode)

if __name__ == "__main__":

    cli()



