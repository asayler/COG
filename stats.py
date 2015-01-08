#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Spring 2015
# University of Colorado

import sys
import cogs.structs

srv = cogs.structs.Server()

def assignment_stats(asn_uuid):

    asn = srv.get_assignment(asn_uuid)

    sub_tot = 0
    run_tot = 0
    submitter_subs = {}
    submitter_runs = {}

    for sub_uuid in asn.list_submissions():

        sub_tot += 1
        sub = srv.get_submission(sub_uuid)
        user_uuid = sub['owner']

        if user_uuid in submitter_subs:
            submitter_subs[user_uuid].append(sub)
        else:
            submitter_subs[user_uuid] = [sub]

        for run_uuid in sub.list_runs():

            run_tot += 1
            run = srv.get_run(run_uuid)

            if user_uuid in submitter_runs:
                submitter_runs[user_uuid].append(run)
            else:
                submitter_runs[user_uuid] = [run]

    sub_cnts = [len(subs) for subs in submitter_subs.values()]
    run_cnts = [len(runs) for runs in submitter_runs.values()]

    print("")
    print(asn['name'])
    print("sub_tot = {}".format(sub_tot))
    print("run_tot = {}".format(run_tot))
    print("run_max = {}".format(max(run_cnts)))
    print("run_min = {}".format(min(run_cnts)))
    # print("run_mean = {}") 
    # print("run_median = {}")
    # print("run_mode = {}")
    print("submitter_subs = {}".format(len(submitter_subs)))
    print("submitter_runs = {}".format(len(submitter_runs)))        

if __name__ == "__main__":

    for asn_uuid in srv.list_assignments():
        assignment_stats(asn_uuid)
