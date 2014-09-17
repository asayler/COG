# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import string
import time

import moodle.ws

import config

EXTRA_REPORTER_SCHEMA = ['moodle_asn_id', 'moodle_respect_duedate']
EXTRA_REPORTER_DEFAULTS = {'moodle_respect_duedate': "1"}

_MAX_COMMENT_LEN = 2000

class RepModMoodleError(Exception):
    """Base class for RepMod Moodle Exceptions"""

    def __init__(self, *args, **kwargs):
        super(RepModMoodleError, self).__init__(*args, **kwargs)


class Reporter(object):

    def __init__(self, rpt):

        # Check Input
        if rpt['mod'] != 'moodle':
            raise RepModMoodleError("Repmod requires report with repmod 'moodle'")

        # Call Parent
        super(Reporter, self).__init__()

        # Save vars
        self.asn_id = rpt['moodle_asn_id']

        # Setup Vars
        self.host = config.REPMOD_MOODLE_HOST

        # Setup WS
        self.ws = moodle.ws.WS(self.host)
        self.ws.authenticate(config.REPMOD_MOODLE_USERNAME,
                             config.REPMOD_MOODLE_PASSWORD,
                             config.REPMOD_MOODLE_SERVICE)

    def file_report(self, user, grade, comment):

        # Check Moodle User
        if user['auth'] != 'moodle':
            raise RepModMoodleError("Repmod requires users with authmod 'moodle'")

        # Check Due Date
        time_due = None
        courses = self.ws.mod_assign_get_assignments([])["courses"]
        for course in courses:
            assignments = course["assignments"]
            for assignment in assignments:
                if (int(assignment["id"]) == int(self.asn_id)):
                    time_due = float(assignment["duedate"])
                if time_due is not None:
                    break
            if time_due is not None:
                break
        if time_due is None:
            raise RepModMoodleError("Could not find assignment {:s}".format(self.asn_id))
        if time_due > 0:
            time_now = time.time()
            if (time_now > time_due):
                time_now_str = time.strftime("%d/%m/%y %H:%M:%S %Z", time.localtime(time_now))
                time_due_str = time.strftime("%d/%m/%y %H:%M:%S %Z", time.localtime(time_due))
                msg = "Current time ({:s}) is past due date ({:s}): ".format(time_now_str, time_due_str)
                msg += "No grade written to Moodle"
                raise RepModMoodleError(msg)

        # Limit Output
        warning = "\nWARNING: Output Truncated"
        max_len = (_MAX_COMMENT_LEN - len(warning))
        if len(comment) > max_len:
            comment = comment[:max_len]
            comment += warning

        asn_id = self.asn_id
        usr_id = user['moodle_id']
        self.ws.mod_assign_save_grade(asn_id, usr_id, grade, comment=comment)
