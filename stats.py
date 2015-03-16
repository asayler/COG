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

        all_runs_by_owner = owners_by_tst[tst_uuid]
        suc_runs_by_owner = {owner: filter(lambda run: not int(run['retcode']),
                                           all_runs_by_owner[owner])
                             for owner in all_runs_by_owner.keys()}
        noz_runs_by_owner = {owner: filter(lambda run: float(run['score']),
                                           all_runs_by_owner[owner])
                             for owner in all_runs_by_owner.keys()}

        all_scores_by_owner = {owner: [float(run['score']) for run in all_runs_by_owner[owner]]
                               for owner in all_runs_by_owner.keys()}
        suc_scores_by_owner = {owner: [float(run['score']) for run in suc_runs_by_owner[owner]]
                               for owner in suc_runs_by_owner.keys()}
        noz_scores_by_owner = {owner: [float(run['score']) for run in noz_runs_by_owner[owner]]
                               for owner in noz_runs_by_owner.keys()}

        all_runs = filter(None, all_runs_by_owner.values())
        suc_runs = filter(None, suc_runs_by_owner.values())
        noz_runs = filter(None, noz_runs_by_owner.values())

        all_scores = filter(None, all_scores_by_owner.values())
        suc_scores = filter(None, suc_scores_by_owner.values())
        noz_scores = filter(None, noz_scores_by_owner.values())

        run_cnts_all = [len(runs) for runs in all_runs]
        run_cnts_suc = [len(runs) for runs in suc_runs]
        run_cnts_noz = [len(runs) for runs in noz_runs]
        raw_scores_all = [i for s in all_scores for i in s]
        raw_scores_suc = [i for s in suc_scores for i in s]
        raw_scores_noz = [i for s in noz_scores for i in s]
        max_scores_all = [max(scores) for scores in all_scores]
        max_scores_suc = [max(scores) for scores in suc_scores]
        max_scores_noz = [max(scores) for scores in noz_scores]
        min_scores_all = [min(scores) for scores in all_scores]
        min_scores_suc = [min(scores) for scores in suc_scores]
        min_scores_noz = [min(scores) for scores in noz_scores]
        dlt_scores_all = [(max(scores) - min(scores)) for scores in all_scores]
        dlt_scores_suc = [(max(scores) - min(scores)) for scores in suc_scores]
        dlt_scores_noz = [(max(scores) - min(scores)) for scores in noz_scores]

        out = {}
        out['info_asn_name'] = asn['name']
        out['info_asn_uuid'] = asn_uuid
        out['info_tst_name'] = tst['name']
        out['info_tst_uuid'] = tst_uuid
        out['meta_max_score'] = float(tst['maxscore'])
        out['meta_tot_subs'] = len(all_runs_by_owner)
        out['stats_run_cnt_all'] = stats(run_cnts_all)
        out['stats_run_cnt_suc'] = stats(run_cnts_suc)
        out['stats_run_cnt_noz'] = stats(run_cnts_noz)
        out['stats_score_raw_all'] = stats(raw_scores_all)
        out['stats_score_raw_suc'] = stats(raw_scores_suc)
        out['stats_score_raw_noz'] = stats(raw_scores_noz)
        out['stats_score_max_all'] = stats(max_scores_all)
        out['stats_score_max_suc'] = stats(max_scores_suc)
        out['stats_score_max_noz'] = stats(max_scores_noz)
        out['stats_score_min_all'] = stats(min_scores_all)
        out['stats_score_min_suc'] = stats(min_scores_suc)
        out['stats_score_min_noz'] = stats(min_scores_noz)
        out['stats_score_dlt_all'] = stats(dlt_scores_all)
        out['stats_score_dlt_suc'] = stats(dlt_scores_suc)
        out['stats_score_dlt_noz'] = stats(dlt_scores_noz)

        return out

def stats(l):

    cnt = 0
    tot = 0.0
    freq = collections.Counter()
    for i in l:
        cnt += 1
        tot += i
        freq[i] += 1
        
    if cnt:
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
    else:
        stats = {}
        stats['avg_mean'] = None
        stats['avg_medn'] = None
        stats['avg_mode'] = None
        stats['vals_max'] = None
        stats['vals_min'] = None
        stats['vals_cnt'] = cnt
        stats['vals_sum'] = tot
        stats['vals_frq'] = None

    return stats

if __name__ == "__main__":

    for asn_uuid in srv.list_assignments():
        out = assignment_stats(asn_uuid)
        print("")
        print("--------------------------------------------------------------------------------")
        pprint.pprint(out)
