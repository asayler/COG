# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import env_local
import tester_script
import tester_io

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
            tester = tester_script.Tester(env, tst.get_dict())
        elif tester_type == 'io':
            tester = tester_io.Tester(env, tst.get_dict())
        else:
            raise Exception("Unknown tester type {:s}".format(tester_type))

        # Run Test
        run['status'] = 'running'
        try:
            ret, score, output = tester.test()
        except:
            status = 'complete-error'
            raise
        else:
            status = 'complete'

    except Exception as e:
        retcode = ""
        score = 0
        output = str(e)
        status = "complete-exception"
        raise
    else:
        retcode = str(ret)
        score = str(score)
        output = str(output)
    finally:

        # Cleanup
        env.close()

        # Update Run
        run['retcode'] = retcode
        run['score'] = score
        run['output'] = output
        run['status'] = status # Must be set last to avoid race
