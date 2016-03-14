#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Spring 2016
# University of Colorado

import cogs.structs

def cleanup_orphaned_files(srv):

    attached = list_attached_files(srv)
    files = srv.list_files()
    orphans = files - attached

    for fle_uid in orphans:
        fle = srv.get_file(fle_uid)
        fle.delete()

    return orphans

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

if __name__ == "__main__":

    srv = cogs.structs.Server()
    
    orphans = cleanup_orphaned_files(srv)
    print("Cleanup up {} orphaned files".format(len(orphans)))
