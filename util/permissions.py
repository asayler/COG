#!/usr/bin/env python

import sys
import uuid

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
              type=click.Path(exists=True, readable=True, resolve_path=True, dir_okay=False),
              help='JSON Permission Spec File Path')
@click.option('--endpoint', '-e', default=None, help='Base Endpoint')
@click.pass_obj
def set_permissions(obj, path, endpoint):
    """Set permissions from json file"""

    cnt = perms.set_perms_from_file(path, endpoint)
    click.echo("Set {} permissions".format(cnt))

@cli.command()
@click.option('--dir', '-d', 'dir_path', default="../perms/",
              type=click.Path(exists=True, readable=True, resolve_path=True, file_okay=False),
              help='JSON Permission Spec Directory Path')
@click.pass_obj
def reset_defaults(dir_path):
    """ Reset all permissions"""
    pass

@cli.command()
@click.pass_obj
def list_admins(obj):
    """List current admins"""

    admin_lst = obj['auth'].list_admins()

    click.echo("Admins:")
    for uid in admin_lst:
        usr = obj['auth'].get_user(uid)
        click.echo(usr['username'])

@cli.command()
@click.argument('usernames', nargs=-1, required=True)
@click.pass_obj
def add_admins(obj, usernames):
    """Add new admins"""

    uid_lst = []
    for username in usernames:
        try:
            usr_uid = uuid.UUID(username)
        except ValueError:
            uid_str = obj['auth'].username_map.lookup_username(username)
            if uid_str:
                usr_uid = uuid.UUID(uid_str)
            else:
                raise click.ClickException("Username '{}' not found".format(username))
        uid_lst.append(usr_uid)

    cnt = obj['auth'].add_admins(uid_lst)
    click.echo("Added {} Admins".format(cnt))

if __name__ == "__main__":
    #pylint: disable=no-value-for-parameter
    sys.exit(cli())
