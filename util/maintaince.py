#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Spring 2016
# University of Colorado

import time

import cogs.structs

ORPHAN_AGE = 3600 #seconds

def cleanup_orphaned_files(srv):

    attached = list_attached_files(srv)
    files = srv.list_files()
    orphans = files - attached
    deleted = set()

    for fle_uid in orphans:
        fle = srv.get_file(fle_uid)
        mod_time = float(fle.get_dict()['modified_time'])
        if (time.time() - mod_time) > ORPHAN_AGE:
            fle.delete()
            deleted.add(fle_uid)

    return deleted

def cleanup_orphaned_reporters(srv):

    attached = list_attached_reporters(srv)
    reporters = srv.list_reporters()
    orphans = reporters - attached
    deleted = set()

    for rpt_uid in orphans:
        rpt = srv.get_reporter(rpt_uid)
        mod_time = float(rpt.get_dict()['modified_time'])
        if (time.time() - mod_time) > ORPHAN_AGE:
            rpt.delete()
            deleted.add(rpt_uid)

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

if __name__ == "__main__":

    srv = cogs.structs.Server()

    orphans = cleanup_orphaned_files(srv)
    print("Cleaned up {} orphaned files".format(len(orphans)))

    orphans = cleanup_orphaned_reporters(srv)
    print("Cleaned up {} orphaned reporters".format(len(orphans)))
