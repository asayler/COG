#!/usr/bin/env python

import sys

import click

import perms

@click.command()

@click.option('--file', '-f', 'path', default="./perms/base.json",
              type=click.Path(exists=True, readable=True, resolve_path=True),
              help='JSON Permission Spec')
@click.option('--endpoint', '-e', default=None, help='Base Endpoint')
def set_permissions(path, endpoint):
    cnt = perms.set_perms_from_file(path, endpoint)
    click.echo("Set {} permissions".format(cnt))

if __name__ == "__main__":
    sys.exit(set_permissions())
