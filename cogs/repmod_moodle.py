# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


import time
import logging

import moodle.ws

import config

import repmod


EXTRA_REPORTER_SCHEMA = ['moodle_asn_id', 'moodle_cm_id',
                         'moodle_respect_duedate', 'moodle_only_higher',
                         'moodle_prereq_asn_id', 'moodle_prereq_cm_id',
                         'moodle_prereq_min']
EXTRA_REPORTER_DEFAULTS = {'moodle_asn_id': "0", 'moodle_cm_id': "0",
                           'moodle_respect_duedate': "1", 'moodle_only_higher': "1",
                           'moodle_prereq_asn_id': "0", 'moodle_prereq_cm_id': "0",
                           'moodle_prereq_min': "0"}

ERS = EXTRA_REPORTER_SCHEMA
ERD = EXTRA_REPORTER_DEFAULTS

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

        # Setup WS
        self.host = config.REPMOD_MOODLE_HOST
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

        # Setup Defaults
        asn_id = int(rpt.get('moodle_asn_id',
                             ERD['moodle_asn_id']))
        cm_id = int(rpt.get('moodle_cm_id',
                            ERD['moodle_cm_id']))
        self.respect_duedate = bool(int(rpt.get('moodle_respect_duedate',
                                                ERD['moodle_respect_duedate'])))
        self.only_higher = bool(int(rpt.get('moodle_only_higher',
                                            ERD['moodle_only_higher'])))
        prereq_asn_id = int(rpt.get('moodle_prereq_asn_id',
                                    ERD['moodle_prereq_asn_id']))
        prereq_cm_id = int(rpt.get('moodle_prereq_cm_id',
                                   ERD['moodle_prereq_cm_id']))
        self.prereq_min = float(rpt.get('moodle_prereq_min',
                                        ERD['moodle_prereq_min']))

        # Get Asn
        self.asn = self._get_asn(asn_id, cm_id)

        # Get Prereq
        if prereq_asn_id or prereq_cm_id:
            self.prereq_asn = self._get_asn(prereq_asn_id, prereq_cm_id)
        else:
            self.prereq_asn = None

    def _get_asn(self, asn_id=None, cm_id=None):

        res = self.ws.mod_assign_get_assignments([])
        asn = None
        if asn_id:
            courses = res['courses']
            for course in courses:
                assignments = course['assignments']
                for assignment in assignments:
                    if (assignment['id'] == asn_id):
                        asn = assignment
                    if asn:
                        break
                if asn:
                    break
            else:
                msg = "repmod_moodle: asn_id '{}' not found".format(asn_id)
                logger.error(self._format_msg(msg))
                raise MoodleReporterError(msg)
        elif cm_id:
            courses = res['courses']
            for course in courses:
                assignments = course['assignments']
                for assignment in assignments:
                    if (assignment['cmid'] == cm_id):
                        asn = assignment
                    if asn:
                        break
                if asn:
                    break
            else:
                msg = "repmod_moodle: cm_id '{}' not found".format(cmid)
                logger.error(self._format_msg(msg))
                raise MoodleReporterError(msg)
        else:
            msg = "repmod_moodle: Requires either an asn_id or a cm_id"
            logger.error(self._format_msg(msg))
            raise MoodleReporterError(msg)
        return asn

    def _get_grade(self, asn_id, usr_id):

        assignments = self.ws.mod_assign_get_grades([asn_id])["assignments"]
        if assignments:
            assignment = assignments.pop()
            grades = assignment['grades']
            grades_by_uid = {}
            for grade in grades:
                uid = int(grade["userid"])
                if uid in grades_by_uid:
                    grades_by_uid[uid].append(grade)
                else:
                    grades_by_uid[uid] = [grade]
            if usr_id in grades_by_uid:
                last_grade = -1.0
                last_num = None
                for attempt in grades_by_uid[usr_id]:
                    num = int(attempt['attemptnumber'])
                    if num > last_num:
                        last_num = num
                        last_grade = float(attempt['grade'])
                return last_grade
            else:
                return None
        else:
            return None

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
        usr_id = int(usr['moodle_id'])
        grade = float(grade)

        # Check Due Date
        if self.respect_duedate:
            time_due = self.asn['duedate']
            if time_due > 0:
                time_now = time.time()
                if (time_now > time_due):
                    time_now_str = time.strftime("%d/%m/%y %H:%M:%S %Z",
                                                 time.localtime(time_now))
                    time_due_str = time.strftime("%d/%m/%y %H:%M:%S %Z",
                                                 time.localtime(time_due))
                    msg = "repmod_moodle: "
                    msg += "Current time ({:s}) ".format(time_now_str)
                    msg += "is past due date ({:s}): ".format(time_due_str)
                    msg += "No grade written to Moodle"
                    logger.warning(self._format_msg(msg))
                    raise MoodleReporterError(msg)

        # Check if grade is higher than prereq min
        if self.prereq_asn:
            try:
                prereq_grade = self._get_grade(self.prereq_asn['id'], usr_id)
            except ValueError as err:
                msg = "repmod_moodle: Could not find prereq assignment {:d}".format(self.prereq_asn['id'])
                logger.error(self._format_msg(msg))
                raise MoodleReporterError(msg)
            if prereq_grade is None:
                msg = "repmod_moodle: "
                msg += "No Assignment {} grade found. ".format(self.prereq_asn['id'])
                msg += "You must complete that assignment before being graded on this one: "
                msg += "No grade written to Moodle"
                logger.warning(self._format_msg(msg))
                raise MoodleReporterError(msg)
            elif prereq_grade < self.prereq_min:
                msg = "repmod_moodle: "
                msg += "Assignment {} grade ({:.2f}) ".format(self.prereq_asn['id'], prereq_grade)
                msg += "is lower than required grade ({:.2f}): ".format(self.prereq_min)
                msg += "No grade written to Moodle"
                logger.warning(self._format_msg(msg))
                raise MoodleReporterError(msg)

        # Check is grade is higher than current
        if self.only_higher:
            prev_grade = self._get_grade(self.asn['id'], usr_id)
            if prev_grade is None:
                pass
            elif grade < prev_grade:
                msg = "repmod_moodle: "
                msg += "Previous grade ({:.2f}) ".format(prev_grade)
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
            self.ws.mod_assign_save_grade(self.asn['id'], usr_id, grade, comment=comment)
        except Exception as e:
            msg = "repmod_moodle: mod_assign_save_grade failed: {:s}".format(e)
            logger.error(self._format_msg(msg))
            raise
