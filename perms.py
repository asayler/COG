import json
import os.path
import uuid
import logging

import cogs.auth

# Constants

GROUP_ALIAS_ANY = ["any", "all", "everyone"]
GROUP_ALIAS_ADMIN = ["admin", "admins", "administrator", "administrators"]

# Logger

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())

# Functions

def ep_norm(ep):

    ep = ep.strip("/")
    ep = "/{:s}".format(ep)
    return "{:s}/".format(os.path.normpath(ep))

def ep_join(*args):

    ep = ""
    for arg in args:
        ep += ep_norm(arg)
    return ep_norm(ep)

def group_norm(group_name):

    group_name = group_name.lower()

    # Any case
    if group_name in GROUP_ALIAS_ANY:
        return cogs.auth.SPECIAL_GROUP_ANY

    # Admin case
    if group_name in GROUP_ALIAS_ADMIN:
        return cogs.auth.SPECIAL_GROUP_ADMIN

    # Other case
    a = cogs.auth.Auth()
    group_objs = [a.get_group(uid) for uid in a.list_groups()]
    group_names = {obj["name"].lower(): str(obj.uuid) for obj in group_objs}

    if group_name in group_names:
        group_uuid = group_names[group_name]
    else:
        group_obj = a.create_group({"name": group_name})
        group_uuid = str(group_obj.uuid)

    return group_uuid

def parse_file(path, ep_base=None):

    # Clean Args
    path = os.path.abspath(path)
    if ep_base:
        ep_base = ep_norm(ep_base)

    # Read file
    js = None
    with open(path, 'r') as f:
        js = json.load(f)

    # Parse JSON
    out = []
    groups = js["groups"]
    for group, perms in groups.iteritems():
        group = group_norm(group)
        for perm in perms:
            if ep_base:
                ep = ep_join(ep_base, perm["ep"])
            else:
                ep = ep_norm(perm["ep"])
            method = perm["method"]
            tup = (method, ep, group)
            out.append(tup)

    # Return
    return out

def set_perms(perms):

    a = cogs.auth.Auth()
    cnt = 0
    for tup in perms:
        method, ep, group = tup
        ret = a.add_allowed_groups(method, ep, [group])
        logger.info("Allow group {} for {} on {} -> {}".format(group, method, ep, ret))
        cnt += ret
    return cnt

def set_perms_from_file(path, ep_base=None):

    perms = parse_file(path, ep_base)
    cnt = set_perms(perms)
    logger.info("Added {} permissions from {}".format(cnt, path))
    return cnt
