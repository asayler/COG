# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import traceback
import time

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
                output = traceback.format_exc()
                status = 'complete-exception-run'
            else:
                if retcode == 0:
                    status = 'complete'
                else:
                    status = 'complete-error'
                retcode = str(retcode)
                score = str(score)
                output = str(output)

                # Report Results
                a = auth.Auth()
                user = a.get_user(sub['owner'])
                grade = score
                comments = "COG Grading Report\n"
                comments += "{:s}\n".format(time.asctime())
                comments += "Assignment: {:s}\n".format(repr(asn))
                comments += "Test: {:s}\n".format(repr(tst))
                comments += "Submission: {:s}\n".format(repr(sub))
                comments += "Run: {:s}\n".format(repr(run))
                comments += "Run Score: {:s} of {:s}\n".format(score, tst['maxscore'])
                comments += "Run Return: {:s}\n".format(retcode)
                comments += "Run Status: {:s}\n".format(status)
                comments += "Run Output:\n"
                comments += output
                for rpt in tst.get_reporters():
                    try:
                        rpt.file_report(user, grade, comments)
                    except Exception as e:
                        output += "\nReporting Failed: {:s}".format(e)
                        status = "complete-exception-reporter"
        # Cleanup
        env.close()

    finally:

        # Update Run
        # TODO Prevent update if run has been deleted
        run['retcode'] = retcode
        run['score'] = score
        run['output'] = output
        run['status'] = status # Must be set last to avoid race
