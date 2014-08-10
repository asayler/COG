# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import moodle.ws

MOODLE_ADDRESS = "https://moodle-test.cs.colorado.edu"
MOODLE_SERVICE = "Grading_Serv"

class AuthMoodle(object):

    def __init__(self):

        # Call Parent
        super(AuthMooddle, self).__init__()

        # Setup Vars
        self.host = MOODLE_ADDRESS
        self.service = MOODLE_SERVICE

    def auth_user(self, username, password):
        moodle = moodle.ws.WS(self.host)
        if moodle.authenticate(usernmae, password, self.service):
            return moodle.getWSUser()
        else:
            return None
