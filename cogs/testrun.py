# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import traceback

import env_local
import tester_script
import tester_io

import auth

def test(asn, sub, tst, run):

    # Setup Env
    try:
        env_type = asn['env']
        if env_type == 'local':
            env = env_local.Env(asn, sub, tst, run)
        else:
            raise Exception("Unknown env type {:s}".format(env_type))
    except Exception as e:
        retcode = -1
        score = 0
        output = traceback.format_exc()
        status = "complete-exception-env"
    else:
        # Setup Tester
        try:
            tester_type = tst['tester']
            if tester_type == 'script':
                tester = tester_script.Tester(env, tst, run)
            elif tester_type == 'io':
                tester = tester_io.Tester(env, tst, run)
            else:
                raise Exception("Unknown tester type {:s}".format(tester_type))
        except Exception as e:
            retcode = -1
            score = 0
            output = traceback.format_exc()
            status = "complete-exception-tst"
        else:
            # Run Test
            try:
                run['status'] = 'running'
                retcode, score, output = tester.test()
            except Exception as e:
                retcode = -1
                score = 0
                output = str(e)
                status = 'complete-error'
            else:
                status = 'complete'
                retcode = str(retcode)
                score = str(score)
                output = str(output)

                # Report Results
                a = auth.Auth()
                user = a.get_user(sub['owner'])
                grade = score
                comments = output
                for rpt in tst.get_reporters():
                    try:
                        rpt.file_report(user, grade, comments)
                    except Exception as e:
                        retcode = -1
                        score = 0
                        output = traceback.format_exc()
                        status = "complete-exception-reporter"
        # Cleanup
        env.close()
    finally:
        # Update Run
        run['retcode'] = retcode
        run['score'] = score
        run['output'] = output
        run['status'] = status # Must be set last to avoid race
