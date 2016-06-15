#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Spring 2016
# University of Colorado

import sys
import time

import cogs.structs
import cogs.auth

ORPHAN_AGE = 3600 #seconds

def cleanup_orphaned_files(srv, test=False):

    attached = list_attached_files(srv)
    files = srv.list_files()
    orphans = files - attached
    deleted = set()

    for fle_uid in orphans:
        fle = srv.get_file(fle_uid)
        mod_time = float(fle['modified_time'])
        if (time.time() - mod_time) > ORPHAN_AGE:
            if not test:
                fle.delete()
            deleted.add(fle_uid)

    return deleted

def cleanup_orphaned_reporters(srv, test=False):

    attached = list_attached_reporters(srv)
    reporters = srv.list_reporters()
    orphans = reporters - attached
    deleted = set()

    for rpt_uid in orphans:
        rpt = srv.get_reporter(rpt_uid)
        mod_time = float(rpt['modified_time'])
        if (time.time() - mod_time) > ORPHAN_AGE:
            if not test:
                rpt.delete()
            deleted.add(rpt_uid)

    return deleted

def cleanup_nonowner_users(srv, auth, test=False):

    owners = list_owners(srv)
    users = auth.list_users()
    admins = auth.list_admins()
    nonowner = users - owners - admins
    deleted = set()

    for usr_uid in nonowner:
        usr = auth.get_user(usr_uid)
        mod_time = float(usr['modified_time'])
        if (time.time() - mod_time) > ORPHAN_AGE:
            if not test:
                usr.delete()
            deleted.add(usr_uid)

    return deleted

def list_attached_files(srv):

    attached = set()

    # From Tests
    tst_uids = srv.list_tests()
    for tst_uid in tst_uids:
        tst = srv.get_test(tst_uid)
        fle_uids = tst.list_files()
        attached.update(fle_uids)

    # From Submission
    sub_uids = srv.list_submissions()
    for sub_uid in sub_uids:
        sub = srv.get_submission(sub_uid)
        fle_uids = sub.list_files()
        attached.update(fle_uids)

    return attached

def list_attached_reporters(srv):

    attached = set()

    # From Tests
    tst_uids = srv.list_tests()
    for tst_uid in tst_uids:
        tst = srv.get_test(tst_uid)
        rpt_uids = tst.list_reporters()
        attached.update(rpt_uids)

    return attached

def list_owners(srv):

    owners = set()

    # From Files
    fle_uids = srv.list_files()
    for fle_uid in fle_uids:
        fle = srv.get_file(fle_uid)
        owners.add(fle['owner'])

    # From Reporters
    rpt_uids = srv.list_reporters()
    for rpt_uid in rpt_uids:
        rpt = srv.get_reporter(rpt_uid)
        owners.add(rpt['owner'])

    # From Assignments
    asn_uids = srv.list_assignments()
    for asn_uid in asn_uids:
        asn = srv.get_assignment(asn_uid)
        owners.add(asn['owner'])

    # From Tests
    tst_uids = srv.list_tests()
    for tst_uid in tst_uids:
        tst = srv.get_test(tst_uid)
        owners.add(tst['owner'])

    # From Submissions
    sub_uids = srv.list_submissions()
    for sub_uid in sub_uids:
        sub = srv.get_submission(sub_uid)
        owners.add(sub['owner'])

    # From Runs
    run_uids = srv.list_runs()
    for run_uid in run_uids:
        run = srv.get_run(run_uid)
        owners.add(run['owner'])

    return owners

if __name__ == "__main__":

    test = False
    srv = cogs.structs.Server()
    auth = cogs.auth.Auth()

    if len(sys.argv) == 1:
        pass
    elif len(sys.argv) == 2:
        if sys.argv[1] == "-t":
            test = True
        else:
            sys.stderr.write("Unknown option: '{}'\n".format(sys.argv[1]))
            sys.exit(1)
    else:
        sys.stderr.write("Too many options\n")
        sys.exit(1)

    print("Cleaning up orphaned files...")
    allfles = srv.list_files()
    orphans = cleanup_orphaned_files(srv, test=test)
    for fle_uid in orphans:
        fle = srv.get_file(fle_uid)
        print("Removed file {}: {}".format(fle_uid, fle['name']))
    print("Cleaned up {} orphaned files of {} total files".format(len(orphans),
                                                                  len(allfles)))

    print("Cleaning up orphaned reporters...")
    allrpts = srv.list_reporters()
    orphans = cleanup_orphaned_reporters(srv, test=test)
    for rpt_uid in orphans:
        rpt = srv.get_reporter(rpt_uid)
        print("Removed reporter {}".format(rpt_uid))
    print("Cleaned up {} orphaned reporters of {} total reporters".format(len(orphans),
                                                                          len(allrpts)))

    print("Cleaning up non-owner users...")
    allusers = auth.list_users()
    nonowners = cleanup_nonowner_users(srv, auth, test=test)
    for usr_uid in nonowners:
        usr = auth.get_user(usr_uid)
        print("Removed user {}: {}".format(usr_uid, usr['username']))
    print("Cleaned up {} non-owner users of {} total users".format(len(nonowners),
                                                                   len(allusers)))

    sys.exit(0)
