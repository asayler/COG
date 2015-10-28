import json
import os.path

import cogs.auth

def ep_norm(ep):

    ep = ep.strip("/")
    ep = "/{:s}".format(ep)
    return "{:s}/".format(os.path.normpath(ep))

def ep_join(*args):

    ep = ""
    for arg in args:
        ep += ep_norm(arg)
    return ep_norm(ep)

def parse_file(path, ep_base=None):

    path = os.path.abspath(path)
    if ep_base:
        ep_base = os.path.normpath(ep_base)

    j = None
    with open(path, 'r') as f:
        j = json.load(f)

    groups = j["groups"]

    for group, perms in groups.iteritems():
        for perm in perms:

            if ep_base:
                ep = ep_join(ep_base, perm["ep"])
            else:
                ep = ep_norm(perm["ep"])

            method = perm["method"]
            group = group

            print(ep)
            print(method)
            print(group)
