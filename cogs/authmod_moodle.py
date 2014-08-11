# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import moodle.ws

MOODLE_ADDRESS = "https://moodle-test.cs.colorado.edu"
MOODLE_SERVICE = "Grading_Serv"

EXTRA_USER_SCHEMA = ['moodle_id', 'moodle_token']

class Authenticator(object):

    def __init__(self):

        # Call Parent
        super(Authenticator, self).__init__()

        # Setup Vars
        self.host = MOODLE_ADDRESS
        self.service = MOODLE_SERVICE

    def auth_user(self, username, password):
        moodlews = moodle.ws.WS(self.host)
        if moodlews.authenticate(username, password, self.service):
            return moodlews.get_WSUser()
        else:
            return None
