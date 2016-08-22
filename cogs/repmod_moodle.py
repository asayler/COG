# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


import time
import logging
import math

import moodle.ws

import config

import repmod


EXTRA_REPORTER_SCHEMA = ['moodle_asn_id', 'moodle_cm_id',
                         'moodle_respect_duedate', 'moodle_only_higher',
                         'moodle_prereq_asn_id', 'moodle_prereq_cm_id',
                         'moodle_prereq_min',
                         'moodle_late_penalty', 'moodle_late_period']
EXTRA_REPORTER_DEFAULTS = {'moodle_asn_id': "0", 'moodle_cm_id': "0",
                           'moodle_respect_duedate': "1", 'moodle_only_higher': "1",
                           'moodle_prereq_asn_id': "0", 'moodle_prereq_cm_id': "0",
                           'moodle_prereq_min': "0",
                           'moodle_late_penalty': "0", 'moodle_late_period': "0"}

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
        d = rpt.get_dict()
        asn_id = int(d.get('moodle_asn_id',
                           ERD['moodle_asn_id']))
        cm_id = int(d.get('moodle_cm_id',
                          ERD['moodle_cm_id']))
        self.respect_duedate = bool(int(d.get('moodle_respect_duedate',
                                              ERD['moodle_respect_duedate'])))
        self.only_higher = bool(int(d.get('moodle_only_higher',
                                          ERD['moodle_only_higher'])))
        prereq_asn_id = int(d.get('moodle_prereq_asn_id',
                                  ERD['moodle_prereq_asn_id']))
        prereq_cm_id = int(d.get('moodle_prereq_cm_id',
                                 ERD['moodle_prereq_cm_id']))
        self.prereq_min = float(d.get('moodle_prereq_min',
                                      ERD['moodle_prereq_min']))
        self.late_penalty = float(d.get('moodle_late_penalty',
                                        ERD['moodle_late_penalty']))
        self.late_period = float(d.get('moodle_late_period',
                                       ERD['moodle_late_period']))

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

    def _check_due(self, grade):

        # Get current time
        time_now = time.time()
        time_now_str = time.strftime("%d/%m/%y %H:%M:%S %Z",
                                     time.localtime(time_now))

        # Get Due Date
        time_due = int(self.asn['duedate'])
        if not time_due:
            msg = "repmod_moodle: "
            msg += "No duedate set - skipping check"
            logger.warning(self._format_msg(msg))
            return grade, msg
        time_due_str = time.strftime("%d/%m/%y %H:%M:%S %Z",
                                     time.localtime(time_due))

        # Get cutoff Date
        time_cut = int(self.asn['cutoffdate'])
        if not time_cut:
            time_cut = time_due
        time_cut_str = time.strftime("%d/%m/%y %H:%M:%S %Z",
                                     time.localtime(time_cut))

        # Past Cutoff Date
        if (time_now > time_cut):

            msg = "repmod_moodle: "
            msg += "Current time ({:s}) ".format(time_now_str)
            msg += "is past cutoff date ({:s}): ".format(time_cut_str)
            msg += "Grade changed to zero."
            logger.warning(self._format_msg(msg))
            return 0, msg

        # Between Due Date and Cutoff Date
        elif (time_now > time_due):

            # Compute Penalty
            if self.late_penalty and self.late_period:
                dur_late = time_now - time_due
                periods = math.ceil(dur_late / self.late_period)
                penalty = periods * self.late_penalty
                msg = "repmod_moodle: "
                msg += "Current time ({:s}) ".format(time_now_str)
                msg += "is past due date ({:s}): ".format(time_due_str)
                msg += "Accessing {} point penalty.".format(penalty)
                if penalty < grade:
                    grade_out = grade - penalty
                else:
                    grade_out = 0
                logger.warning(self._format_msg(msg))
                return grade_out, msg
            else:
                msg = "repmod_moodle: "
                msg += "Current time ({:s}) ".format(time_now_str)
                msg += "is past due date ({:s}): ".format(time_due_str)
                msg += "Grade changed to zero."
                logger.warning(self._format_msg(msg))
                return 0, msg

        # Before Due Date
        else:
            return grade, None

    def file_report(self, usr, grade, comment):

        # Call Parent
        messages = []
        super(Reporter, self).file_report(usr, grade, comment)
        msg = "repmod_moodle: Filing report for user {:s}".format(usr['username'])
        messages.append(msg)
        logger.info(self._format_msg(msg))

        # Check Moodle or LDAP User
        if usr['auth'] != 'moodle' and usr['auth'] != 'ldap':
            msg = "repmod_moodle: Requires user with authmod 'moodle' or 'ldap'"
            logger.error(self._format_msg(msg))
            raise MoodleReporterError(msg)

        # Extract Vars
        result = self.ws.core_user_get_users([('username', usr['username'])])
        moodle_usr_list = result['users']
        if len(moodle_usr_list) < 1:
            msg = "repmod_moodle: Username not found"
            logger.error(self._format_msg(msg))
            raise MoodleReporterError(msg)
        elif len(moodle_usr_list) > 1:
            msg = "repmod_moodle: multiple users found"
            logger.error(self._format_msg(msg))
            raise MoodleReporterError(msg)
        moodle_usr = moodle_usr_list[0]
        usr_id = int(moodle_usr['id'])
        grade = float(grade)

        # Check Due Date
        if self.respect_duedate:
            grade, msg = self._check_due(grade)
            if msg:
                messages.append(msg)

        # Check if prereq grade is higher than prereq min
        if self.prereq_asn:
            try:
                prereq_grade = self._get_grade(self.prereq_asn['id'], usr_id)
            except ValueError as err:
                msg = "repmod_moodle: "
                msg += "Could not find prereq assignment {:d}".format(self.prereq_asn['id'])
                logger.error(self._format_msg(msg))
                raise MoodleReporterError(msg)
            if prereq_grade is None:
                msg = "repmod_moodle: "
                msg += "No Assignment {} grade found.\n".format(self.prereq_asn['id'])
                msg += "You must complete that assignment before being graded on this one:\n"
                msg += "Grade changed to zero."
                logger.warning(self._format_msg(msg))
                messages.append(msg)
                grade = 0
            elif prereq_grade < self.prereq_min:
                msg = "repmod_moodle: "
                msg += "Assignment {} grade ({:.2f}) ".format(self.prereq_asn['id'], prereq_grade)
                msg += "is lower than required grade ({:.2f}):\n".format(self.prereq_min)
                msg += "Grade changed to zero"
                logger.warning(self._format_msg(msg))
                messages.append(msg)
                grade = 0

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
                return grade, "\n".join(messages)

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

        # Return
        return grade, "\n".join(messages)
