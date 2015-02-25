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

        logger.info("AUTH_INFO: Starting auth for {:s}".format(username))
        moodlews = moodle.ws.WS(self.host)

        try:
            logger.info("AUTH_ATTEMPT: Trying {:s}".format(username))
            ret = moodlews.authenticate(username, password, self.service, error=True)
        except moodle.ws.WSAuthError as e:
            logger.error("AUTH_ERROR: Failed {:s} - {:s}".format(username, e))
            ret = False
        except moodle.ws.WSError as e:
            logger.error("MOODLEWS_ERROR: {:s}".format(e))
            ret = False

        if ret:
            logger.info("AUTH_ALLOWED: Authenticated {:s}".format(username))
            try:
                logger.info("AUTH_INFO: Getting info for {:s}".format(username))
                ret = moodlews.get_WSUser()
            except moodle.ws.WSError as e:
                logger.error("MOODLEWS_ERROR: {:s}".format(e))
                ret = None
        else:
            logger.warning("AUTH_DENIED: Denied {:s}".format(username))
            ret = None

        logger.info("AUTH_INFO: Completed auth for {:s}".format(username))
        return ret
