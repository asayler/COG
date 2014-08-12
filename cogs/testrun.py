# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import env_local
import tester_script

def test(asn, sub, tst, run):

    env_type = asn['env']
    if env_type == 'local':
        env = env_local.Env(asn, sub, tst, run)
    else:
        raise Exception("Unknown env type {:s}".format(env_type))

    tester_type = tst['tester']
    if tester_type == 'script':
        tester = tester_script.Tester(env)
    else:
        raise Exception("Unknown tester type {:s}".format(tester_type))

    run['status'] = 'running'
    try:
        ret, score, output = tester.test()
    except:
        run['status'] = 'complete-error'
        raise
    else:
        run['status'] = 'complete'

    env.close()

    run['retcode'] = str(ret)
    run['score'] = str(score)
    run['output'] = str(output)
