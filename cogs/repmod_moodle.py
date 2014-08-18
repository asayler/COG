# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import moodle.ws

import config

EXTRA_REPORTER_SCHEMA = ['asn_id']

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
        self.asn_id = rpt['asn_id']

        # Setup Vars
        self.host = config.REPMOD_MOODLE_HOST

        # Setup WS
        self.ws = moodle.ws.WS(self.host)
        self.ws.authenticate(config.REPMOD_MOODLE_USERNAME,
                             config.REPMOD_MOODLE_PASSWORD,
                             config.REPMOD_MOODLE_SERVICE)

    def file_report(self, user, grade, comment):

        if user['auth'] != 'moodle':
            raise RepModMoodleError("Repmod requires users with authmod 'moodle'")

        asn_id = self.asn_id
        usr_id = user['moodle_id']
        self.ws.mod_assign_save_grade(asn_id, usr_id, grade, comment=comment)
