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

    submitter_subs = {}
    submitter_runs = {}

    for sub_uuid in asn.list_submissions():

        sub = srv.get_submission(sub_uuid)
        user_uuid = sub['owner']

        if user_uuid in submitter_subs:
            submitter_subs[user_uuid].append(sub)
        else:
            submitter_subs[user_uuid] = [sub]

        for run_uuid in sub.list_runs():

            run = srv.get_run(run_uuid)

            if user_uuid in submitter_runs:
                submitter_runs[user_uuid].append(run)
            else:
                submitter_runs[user_uuid] = [run]

    sub_cnts = [len(subs) for subs in submitter_subs.values()]
    sub_cnt_avgs = averages(sub_cnts)

    run_cnts = [len(runs) for runs in submitter_runs.values()]
    run_cnt_avgs = averages(run_cnts)

    print("")
    print(asn['name'])

    print("sub_submitters = {:d}".format(len(submitter_subs)))
    print("sub_cnt_tot = {:d}".format(sum(sub_cnts)))
    print("sub_cnt_max = {:d}".format(max(sub_cnts)))
    print("sub_cnt_min = {:d}".format(min(sub_cnts)))
    print("sub_cnt_mean = {:.2f}".format(sub_cnt_avgs[0])) 
    print("sub_cnt_medn = {:d}".format(sub_cnt_avgs[1]))
    print("sub_cnt_mode = {}".format(sub_cnt_avgs[2]))

    print("run_submitters = {:d}".format(len(submitter_runs)))
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
