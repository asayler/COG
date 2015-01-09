#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Spring 2015
# University of Colorado

import sys
import collections

import cogs.structs

srv = cogs.structs.Server()

def assignment_stats(asn_uuid):

    asn = srv.get_assignment(asn_uuid)

    owners_by_tst = {tst_uuid:{} for tst_uuid in asn.list_tests()}

    for sub_uuid in asn.list_submissions():

        sub = srv.get_submission(sub_uuid)
        owner_uuid = sub['owner']

        for run_uuid in sub.list_runs():

            run = srv.get_run(run_uuid)
            tst_uuid = run['test']

            if owner_uuid in owners_by_tst[tst_uuid]:
                owners_by_tst[tst_uuid][owner_uuid].append(run)
            else:
                owners_by_tst[tst_uuid][owner_uuid] = [run]

    for tst_uuid in owners_by_tst:

        tst = srv.get_test(tst_uuid)
        runs_by_owner = owners_by_tst[tst_uuid]

        run_cnts = [len(runs) for runs in runs_by_owner.values()]
        run_cnt_avgs = averages(run_cnts)


        print("")
        print("{:s} ({:s})".format(asn['name'], asn_uuid))
        print("{:s} ({:s})".format(tst['name'], tst_uuid))
        print("submitters = {:d}".format(len(runs_by_owner)))
        print("run_cnt_tot = {:d}".format(sum(run_cnts)))
        print("run_cnt_max = {:d}".format(max(run_cnts)))
        print("run_cnt_min = {:d}".format(min(run_cnts)))
        print("run_cnt_mean = {:.2f}".format(run_cnt_avgs[0])) 
        print("run_cnt_medn = {:d}".format(run_cnt_avgs[1]))
        print("run_cnt_mode = {}".format(run_cnt_avgs[2]))

def averages(l):

    cnt = 0
    tot = 0.0
    freq = collections.Counter()
    for i in l:
        cnt += 1
        tot += i
        freq[i] += 1
        
    mean = tot/cnt
    median = sorted(l)[cnt/2]
    common = freq.most_common()
    modes = []
    for i in common:
        if (i[1] == common[0][1]):
            modes.append(i[0])
        else:
            break
    
    return (mean, median, modes)

if __name__ == "__main__":

    for asn_uuid in srv.list_assignments():
        assignment_stats(asn_uuid)
