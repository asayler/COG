#!/usr/bin/env python

import sys

import click

import perms
import cogs.auth

@click.group()
@click.pass_context
def cli(ctx):
    """COG Server Permissions CLI"""

    # Setup Context
    ctx.obj = {}
    ctx.obj['auth'] = cogs.auth.Auth()

@cli.command()
@click.option('--file', '-f', 'path', default="../perms/base.json",
              type=click.Path(exists=True, readable=True, resolve_path=True),
              help='JSON Permission Spec File Path')
@click.option('--endpoint', '-e', default=None, help='Base Endpoint')
@click.pass_obj
def set_permissions(obj, path, endpoint):
    """Set permissions from json file"""

    cnt = perms.set_perms_from_file(path, endpoint)
    click.echo("Set {} permissions".format(cnt))

@cli.command()
@click.pass_obj
def list_admins(obj):
    """List current admins"""

    uid_lst = obj['auth'].list_admins()

    for uid in uid_lst:
        usr = obj['auth'].get_user(uid)
        click.echo(usr['username'])

if __name__ == "__main__":
    #pylint: disable=no-value-for-parameter
    sys.exit(cli())
