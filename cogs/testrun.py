# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import env_local
import tester_script

def test(asn, sub, tst, run):

    try:
        # Setup Env
        env_type = asn['env']
        if env_type == 'local':
            env = env_local.Env(asn, sub, tst, run)
        else:
            raise Exception("Unknown env type {:s}".format(env_type))

        # Setup Tester
        tester_type = tst['tester']
        if tester_type == 'script':
            tester = tester_script.Tester(env)
        else:
            raise Exception("Unknown tester type {:s}".format(tester_type))

        # Run Test
        run['status'] = 'running'
        try:
            ret, score, output = tester.test()
        except:
            run['status'] = 'complete-error'
            raise
        else:
            run['status'] = 'complete'
    except Exception as e:
        run['status'] = "complete-exception"
        run['output'] = str(e)
        raise
    else:
        run['retcode'] = str(ret)
        run['score'] = str(score)
        run['output'] = str(output)
    finally:
        env.close()
