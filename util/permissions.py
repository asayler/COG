#!/usr/bin/env python

import sys
import uuid
import os.path

import click

import perms
import cogs.auth
import cogs.structs
import cogs.config

_FILES_KEY = "files"
_REPORTERS_KEY = "reporters"
_ASSIGNMENTS_KEY = "assignments"
_TESTS_KEY = "tests"
_SUBMISSIONS_KEY = "submissions"
_RUNS_KEY = "runs"

@click.group()
@click.pass_context
def cli(ctx):
    """COG Server Permissions CLI"""

    # Setup Context
    ctx.obj = {}
    ctx.obj['auth'] = cogs.auth.Auth()
    ctx.obj['server'] = cogs.structs.Server()

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
@click.pass_obj
def reset_defaults(obj):
    """ Reset all permissions"""

    click.echo("Listing existing permissions")
    perm_lst = obj['auth'].AllowedGroupsFactory.list_family()
    for perm_key in perm_lst:
        click.echo("Permission '{}'".format(perm_key))

    click.echo("Removing existing permissions")
    cnt = 0
    for perm_key in perm_lst:
        perm_obj = obj['auth'].AllowedGroupsFactory.from_raw(key=perm_key)
        perm_obj.delete()
        cnt += 1
    click.echo("Removed {} existing permissions".format(cnt))

    click.echo("Setting base permissions")
    perms_base_path = os.path.join(cogs.config.PERMS_PATH, "base.json")
    if os.path.isfile(perms_base_path):
        cnt = perms.set_perms_from_file(perms_base_path)
    else:
        cnt = 0
    click.echo("Set {} base permissions".format(cnt))

    click.echo("Setting file permissions")
    fle_lst = obj['server'].list_files()
    cnt = perms.create_perms(fle_lst, _FILES_KEY)
    cnt_per = cnt/len(fle_lst) if fle_lst else 0
    click.echo("Set {} file permissions ({} per file)".format(cnt, cnt_per))

    click.echo("Setting reporter permissions")
    rpt_lst = obj['server'].list_reporters()
    cnt = perms.create_perms(rpt_lst, _REPORTERS_KEY)
    cnt_per = cnt/len(rpt_lst) if rpt_lst else 0
    click.echo("Set {} reporter permissions ({} per reporter)".format(cnt, cnt_per))

    click.echo("Setting assignment permissions")
    asn_lst = obj['server'].list_assignments()
    cnt = perms.create_perms(asn_lst, _ASSIGNMENTS_KEY)
    cnt_per = cnt/len(asn_lst) if asn_lst else 0
    click.echo("Set {} assignment permissions ({} per assignment)".format(cnt, cnt_per))

    click.echo("Setting test permissions")
    tst_lst = obj['server'].list_tests()
    cnt = perms.create_perms(tst_lst, _TESTS_KEY)
    cnt_per = cnt/len(tst_lst) if tst_lst else 0
    click.echo("Set {} test permissions ({} per test)".format(cnt, cnt_per))

    click.echo("Setting submission permissions")
    sub_lst = obj['server'].list_submissions()
    cnt = perms.create_perms(sub_lst, _SUBMISSIONS_KEY)
    cnt_per = cnt/len(sub_lst) if sub_lst else 0
    click.echo("Set {} submission permissions ({} per submission)".format(cnt, cnt_per))

    click.echo("Setting run permissions")
    run_lst = obj['server'].list_runs()
    cnt = perms.create_perms(run_lst, _RUNS_KEY)
    cnt_per = cnt/len(run_lst) if run_lst else 0
    click.echo("Set {} run permissions ({} per run)".format(cnt, cnt_per))

    click.echo("Listing new permissions")
    perm_lst = obj['auth'].AllowedGroupsFactory.list_family()
    for perm_key in perm_lst:
        click.echo("Permission '{}'".format(perm_key))

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

@cli.command()
@click.argument('usernames', nargs=-1, required=True)
@click.pass_obj
def rem_admins(obj, usernames):
    """Remove admins"""

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

    cnt = obj['auth'].rem_admins(uid_lst)
    click.echo("Removed {} Admins".format(cnt))

if __name__ == "__main__":
    #pylint: disable=no-value-for-parameter
    sys.exit(cli())
