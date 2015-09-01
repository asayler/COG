#!/usr/bin/env python

import sys

import cogs.auth

def set_default_permissions(asn_uuid, tst_uuid):

    action = "GET"
    endpoint = "/assignments/{:s}/".format(asn_uuid)
    set_endpoint_permissions(action, endpoint)

    action = "GET"
    endpoint = "/assignments/{:s}/tests/".format(asn_uuid)
    set_endpoint_permissions(action, endpoint)

    action = "POST"
    endpoint = "/assignments/{:s}/submissions/".format(asn_uuid)
    set_endpoint_permissions(action, endpoint)

    action = "GET"
    endpoint = "/tests/{:s}/".format(tst_uuid)
    set_endpoint_permissions(action, endpoint)

def set_endpoint_permissions(action, endpoint):

    a = cogs.auth.Auth()
    ret = a.add_allowed_groups(action, endpoint, [cogs.auth.SPECIAL_GROUP_ANY])
    if ret == 0:
        print("'{:s}' already allows {:s}".format(endpoint, action))
    elif ret > 1:
        print("{:s} '{:s}' returned > 1".format(action, endpoint))

if __name__ == "__main__":

    sys.exit(set_default_permissions(*sys.argv[1:]))
