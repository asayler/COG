# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


import time
import logging

import moodle.ws

import config

import repmod


EXTRA_REPORTER_SCHEMA = ['moodle_asn_id', 'moodle_respect_duedate', 'moodle_only_higher']
EXTRA_REPORTER_DEFAULTS = {'moodle_respect_duedate': "1", 'moodle_only_higher': "1"}

_MAX_COMMENT_LEN = 2000
_FLOAT_MARGIN = 0.01

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


class MoodleReporterError(repmod.ReporterError):
    """Base class for Moodle Reporter Exceptions"""

    def __init__(self, *args, **kwargs):

        # Call Parent
        super(MoodleReporterError, self).__init__(*args, **kwargs)


class Reporter(repmod.Reporter):

    def __init__(self, rpt, run):

        # Call Parent
        super(Reporter, self).__init__(rpt, run)
        msg = "repmod_moodle: Initializing reporter {:s}".format(rpt)
        logger.info(self._format_msg(msg))

        # Check Input
        if rpt['mod'] != 'moodle':
            msg = "repmod_moodle: Requires reporter with repmod 'moodle'"
            logger.error(self._format_msg(msg))
            raise MoodleReporterError(msg)

        # Save vars
        self.asn_id = rpt['moodle_asn_id']

        # Setup Vars
        self.host = config.REPMOD_MOODLE_HOST

        # Setup WS
        self.ws = moodle.ws.WS(self.host)
        try:
            self.ws.authenticate(config.REPMOD_MOODLE_USERNAME,
                                 config.REPMOD_MOODLE_PASSWORD,
                                 config.REPMOD_MOODLE_SERVICE,
                                 error=True)
        except Exception as e:
            msg = "repmod_moodle: authenticate failed: {:s}".format(e)
            logger.error(self._format_msg(msg))
            raise

    def file_report(self, usr, grade, comment):

        # Call Parent
        super(Reporter, self).file_report(usr, grade, comment)
        msg = "repmod_moodle: Filing report for user {:s}".format(usr)
        logger.info(self._format_msg(msg))

        # Check Moodle User
        if usr['auth'] != 'moodle':
            msg = "repmod_moodle: Requires user with authmod 'moodle'"
            logger.error(self._format_msg(msg))
            raise MoodleReporterError(msg)

        # Extract Vars
        asn_id = int(self.asn_id)
        usr_id = int(usr['moodle_id'])

        # Check Due Date
        if 'moodle_respect_duedate' in self._rpt:
            respect_duedate = bool(int(self._rpt['moodle_respect_duedate']))
        else:
            respect_duedate = bool(int(EXTRA_REPORTER_DEFAULTS['moodle_respect_duedate']))
        if respect_duedate:
            time_due = None
            courses = self.ws.mod_assign_get_assignments([])["courses"]
            for course in courses:
                assignments = course["assignments"]
                for assignment in assignments:
                    if (int(assignment["id"]) == int(asn_id)):
                        time_due = float(assignment["duedate"])
                    if time_due is not None:
                        break
                if time_due is not None:
                    break
            if time_due is None:
                msg = "repmod_moodle: Could not find assignment {:d}".format(asn_id)
                logger.error(self._format_msg(msg))
                raise MoodleReporterError(msg)
            if time_due > 0:
                time_now = time.time()
                if (time_now > time_due):
                    time_now_str = time.strftime("%d/%m/%y %H:%M:%S %Z", time.localtime(time_now))
                    time_due_str = time.strftime("%d/%m/%y %H:%M:%S %Z", time.localtime(time_due))
                    msg = "repmod_moodle: "
                    msg += "Current time ({:s}) ".format(time_now_str)
                    msg += "is past due date ({:s}): ".format(time_due_str)
                    msg += "No grade written to Moodle"
                    logger.warning(self._format_msg(msg))
                    raise MoodleReporterError(msg)

        # Check is grade is higher than current
        if 'moodle_only_higher' in self._rpt:
            only_higher = bool(int(self._rpt['moodle_only_higher']))
        else:
            only_higher = bool(int(EXTRA_REPORTER_DEFAULTS['moodle_only_higher']))
        if only_higher:
            assignments = self.ws.mod_assign_get_grades([asn_id])["assignments"]
            if len(assignments):
                assignment = assignments.pop()
                old_grades = assignment['grades']
                old_grades_by_uid = {}
                for old_grade in old_grades:
                    uid = int(old_grade["userid"])
                    if uid in old_grades_by_uid:
                        old_grades_by_uid[uid].append(old_grade)
                    else:
                        old_grades_by_uid[uid] = [old_grade]
                if usr_id in old_grades_by_uid:
                    last_grade = None
                    last_num = None
                    for attempt in old_grades_by_uid[usr_id]:
                        num = int(attempt['attemptnumber'])
                        if num > last_num:
                            last_num = num
                            last_grade = float(attempt['grade'])
                    if grade < last_grade:
                        msg = "repmod_moodle: "
                        msg += "Previous grade ({:.2f}) ".format(last_grade)
                        msg += "is greater than current grade ({:.2f}): ".format(grade)
                        msg += "No grade written to Moodle"
                        logger.warning(self._format_msg(msg))
                        raise MoodleReporterError(msg)

        # Limit Output
        warning = "\nWARNING: Output Truncated"
        max_len = (_MAX_COMMENT_LEN - len(warning))
        if len(comment) > max_len:
            comment = comment[:max_len]
            comment += warning

        # Log Grade
        try:
            self.ws.mod_assign_save_grade(asn_id, usr_id, grade, comment=comment)
        except Exception as e:
            msg = "repmod_moodle: mod_assign_save_grade failed: {:s}".format(e)
            logger.error(self._format_msg(msg))
            raise
