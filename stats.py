#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Spring 2015
# University of Colorado

import sys
import collections
import pprint

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
        run_cnt_avgs, run_cnt_freqs = averages(run_cnts)

        scores_by_owner = {owner: [float(run['score']) for run in runs_by_owner[owner]]
                           for owner in runs_by_owner.keys()}
        max_scores = [max(scores) for scores in scores_by_owner.values()]
        max_score_avgs, max_score_freqs = averages(max_scores)
        min_scores = [min(scores) for scores in scores_by_owner.values()]
        min_score_avgs, min_score_freqs = averages(min_scores)

        scores_nonz = filter(None, [filter(None, scores) for scores in scores_by_owner.values()])
        min_scores_nonz = [min(scores) for scores in scores_nonz]
        min_score_nonz_avgs, min_score_nonz_freqs = averages(min_scores_nonz)
        
        print("")
        print("Assignment: {:s} ({:s})".format(asn['name'], asn_uuid))
        print("Test: {:s} ({:s})".format(tst['name'], tst_uuid))
        print("Score Limit: {:s}".format(tst['maxscore']))
        print("submitters = {:d}".format(len(runs_by_owner)))

        print("Run Count Stats:")
        print("Total = {:d}".format(sum(run_cnts)))
        print("Freqs = {}".format(run_cnt_freqs))
        print_stats(run_cnt_avgs)

        print("Max Score Stats:")
        print("Freqs = {}".format(max_score_freqs))
        print_stats(max_score_avgs)

        print("Min Score Stats:")
        print("Freqs = {}".format(min_score_freqs))
        print_stats(min_score_avgs)

        print("Min Score (Non-Zero) Stats:")
        print("Freqs = {}".format(min_score_nonz_freqs))
        print_stats(min_score_nonz_avgs)

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
    
    return ((mean, median, modes, max(l), min(l)), dict(freq))

def print_stats(avgs):

    print("Max = {:.2f}".format(avgs[3]))
    print("Min = {:.2f}".format(avgs[4]))
    print("Mean = {:.2f}".format(avgs[0])) 
    print("Median = {:.2f}".format(avgs[1]))
    print("Modes = {}".format(avgs[2]))


if __name__ == "__main__":

    for asn_uuid in srv.list_assignments():
        assignment_stats(asn_uuid)
