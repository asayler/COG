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
        scores_by_owner = {owner: [float(run['score']) for run in runs_by_owner[owner]]
                           for owner in runs_by_owner.keys()}

        run_cnts = [len(runs) for runs in runs_by_owner.values()]
        max_scores = [max(scores) for scores in scores_by_owner.values()]
        min_scores = [min(scores) for scores in scores_by_owner.values()]
        scores_nonz = filter(None, [filter(None, scores) for scores in scores_by_owner.values()])
        min_scores_nonz = [min(scores) for scores in scores_nonz]
        
        out = {}
        out['info_asn_name'] = asn['name']
        out['info_asn_uuid'] = asn_uuid
        out['info_tst_name'] = tst['name']
        out['info_tst_uuid'] = tst_uuid
        out['info_score_limit'] = float(tst['maxscore'])
        out['info_tot_submitters'] = len(runs_by_owner)
        out['stats_run_cnt'] = stats(run_cnts)
        out['stats_max_score'] = stats(max_scores)
        out['stats_min_score'] = stats(min_scores)
        out['stats_min_score_nonzero'] = stats(min_scores_nonz)
        pprint.pprint(out)

def stats(l):

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

    stats = {}
    stats['avg_mean'] = mean
    stats['avg_medn'] = median
    stats['avg_mode'] = modes
    stats['vals_max'] = max(l)
    stats['vals_min'] = min(l)
    stats['vals_cnt'] = cnt
    stats['vals_sum'] = tot
    stats['vals_frq'] = dict(freq)

    return stats

if __name__ == "__main__":

    for asn_uuid in srv.list_assignments():
        assignment_stats(asn_uuid)
