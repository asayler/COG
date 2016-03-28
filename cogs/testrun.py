# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import traceback
import time
import logging

import config
import env_local
import builder_make
import builder_cmd
import tester_script
import tester_io
import repmod

import auth


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


def test(asn, sub, tst, run):

    # Init
    run['status'] = 'initializing_test'
    retcode = 0
    score = 0.0
    env = None

    # Setup Env
    if (retcode == 0):
        try:
            run['status'] = 'initializing_env'
            env_type = asn['env']
            if env_type == 'local':
                env = env_local.Env(asn, sub, tst, run)
            else:
                raise Exception("Unknown env type {:s}".format(env_type))
        except Exception as e:
            retcode = -1
            score = 0.0
            output = traceback.format_exc()
            status = "complete-exception-env"
            msg = "{}:\n{}".format(status, output)
            logger.error(msg)

    # Setup Builder
    if (retcode == 0):
        try:
            run['status'] = 'initializing_build'
            builder_type = tst['builder']
            if builder_type == '':
                builder = None
            elif builder_type == 'make':
                builder = builder_make.Builder(env, tst, run)
            elif builder_type == 'cmd':
                builder = builder_cmd.Builder(env, tst, run)
            else:
                raise Exception("Unknown builder type {:s}".format(builder_type))
        except Exception as e:
            retcode = -1
            score = 0.0
            output = traceback.format_exc()
            status = "complete-exception-builder_setup"
            msg = "{}:\n{}".format(status, output)
            logger.warning(msg)

    # Run Build (If Necessary)
    if (retcode == 0) and builder:
        try:
            run['status'] = 'building'
            retcode, output = builder.build()
        except Exception as e:
            retcode = -1
            score = 0.0
            output = traceback.format_exc()
            status = 'complete-exception-builder_build'
            msg = "{}:\n{}".format(status, output)
            logger.warning(msg)
        else:
            if (retcode != 0):
                score = 0.0
                status = 'complete-error-builder_build'
                msg = "{}".format(status)
                logger.warning(msg)

    # Setup Tester
    if (retcode == 0):
        try:
            run['status'] = 'initializing_run'
            tester_type = tst['tester']
            if tester_type == 'script':
                tester = tester_script.Tester(env, tst, run)
            elif tester_type == 'io':
                tester = tester_io.Tester(env, tst, run)
            else:
                raise Exception("Unknown tester type {:s}".format(tester_type))
        except Exception as e:
            retcode = -1
            score = 0.0
            output = traceback.format_exc()
            status = "complete-exception-tester_setup"
            msg = "{}:\n{}".format(status, output)
            logger.warning(msg)

    # Run Test
    if (retcode == 0) and tester:
        try:
            run['status'] = 'running'
            retcode, score, output = tester.test()
        except Exception as e:
            retcode = -1
            score = 0.0
            output = traceback.format_exc()
            status = 'complete-exception-tester_run'
            msg = "{}:\n{}".format(status, output)
            logger.warning(msg)
        else:
            if (retcode != 0):
                score = 0
                status = 'complete-error-tester_run'
                msg = "{}".format(status)
                logger.warning(msg)

    # Normalize Results
    if retcode == 0:
        status = 'complete'
    retcode = int(retcode)
    score = float(score)
    output = str(output)

    # Limit output size
    olen = len(output)
    mlen = config.CORE_MAX_OUTPUT
    if olen > mlen:
        msg = "Output length '{}' exceeds max of '{}'. Truncating...".format(olen, mlen)
        logger.warning(msg)
        output = output[:config.CORE_MAX_OUTPUT]
        output += "\n" + msg

    # Report Results
    reporters = tst.get_reporters()
    if reporters:
        run['status'] = 'reporting'
        a = auth.Auth()
        user = a.get_user(sub['owner'])
        comments = "COG Grading Report\n"
        comments += "{:s}\n".format(time.strftime("%a %d %b %Y %H:%M:%S %Z"))
        comments += "Assignment: {:s}\n".format(repr(asn))
        comments += "Test: {:s}\n".format(repr(tst))
        comments += "Submission: {:s}\n".format(repr(sub))
        comments += "Run: {:s}\n".format(repr(run))
        comments += "Run Score: {:.2f} of {:.2f}\n".format(score, float(tst['maxscore']))
        comments += "Run Return: {:d}\n".format(retcode)
        comments += "Run Status: {:s}\n".format(status)
        comments += "Run Output:\n"
        comments += output
        for rpt in tst.get_reporters():
            try:
                score_out, extra_output = rpt.file_report(run, user, score, comments)
                if extra_output:
                    output += "\n" + extra_output
            except Exception as e:
                msg = "WARNING: Reporter Error: {:s}".format(e)
                msg += "\n{}".format(traceback.format_exc())
                output += "\n" + msg
                status = "complete-error-reporter"
                logger.error(msg)
            else:
                if score_out != score:
                    msg = "WARNING: "
                    msg += "Grader lowered score from {:.2f} to {:.2f}".format(score, score_out)
                    output += "\n" + msg
                    status = "complete-warning-reporter"
                    logger.info(msg)
                    score = score_out

    # Cleanup
    run['status'] = 'cleaning_up'
    if env:
        env.close()

    # Update Run
    run['status'] = 'saving'
    # TODO Prevent update if run has been deleted
    run['retcode'] = retcode
    run['score'] = score
    run['output'] = output
    run['status'] = status # Must be set last to avoid race
