# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import logging

import moodle.ws

import config

EXTRA_USER_SCHEMA = ['moodle_id', 'moodle_token']

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())

class Authenticator(object):

    def __init__(self):

        # Call Parent
        super(Authenticator, self).__init__()

        # Setup Vars
        self.host = config.AUTHMOD_MOODLE_HOST
        self.service = config.AUTHMOD_MOODLE_SERVICE

    def auth_user(self, username, password):

        moodlews = moodle.ws.WS(self.host)

        try:
            ret = moodlews.authenticate(username, password, self.service, error=True)
        except moodle.ws.WSAuthError as e:
            logger.error("AUTH_ERROR: {:s}".format(e))
            ret = False
        except moodle.ws.WSError as e:
            logger.error("MOODLEWS_ERROR: {:s}".format(e))
            ret = False

        if ret:
            logger.info("AUTH_ALLOWED {:s}".format(username))
            try:
                ret = moodlews.get_WSUser()
            except moodle.ws.WSError as e:
                logger.error("MOODLEWS_ERROR: {:s}".format(e))
                ret = None
        else:
            logger.warning("AUTH_DENIED {:s}".format(username))
            ret = None

        return ret
