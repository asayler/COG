# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# University of Colorado

import logging

import ldap

import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())

EXTRA_USER_SCHEMA = []

class Authenticator(object):

    def __init__(self):

        # Call Parent
        super(Authenticator, self).__init__()

        # Setup Vars
        self.host = config.AUTHMOD_LDAP_HOST
        self.basedn = config.AUTHMOD_LDAP_BASEDN

    def auth_user(self, username, password):

        user_dn = "uid="+username+","+self.basedn
        base_dn = self.basedn

        logger.info("AUTH_INFO: Starting auth for {:s} as {:s}".format(username, user_dn))

        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        logger.info("AUTH_INFO: Connecting to {:s}".format(self.host))
        l = ldap.initialize(self.host)
        l.set_option(ldap.OPT_REFERRALS, 0)
        l.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        l.set_option(ldap.OPT_X_TLS,ldap.OPT_X_TLS_DEMAND)
        l.set_option( ldap.OPT_X_TLS_DEMAND, True )
        l.set_option( ldap.OPT_DEBUG_LEVEL, 255 )

        search_filter = "uid="+username

        try:
            logger.info("AUTH_ATTEMPT: Trying {:s}".format(user_dn))
            l.bind_s(user_dn,password)
            logger.info("AUTH_ATTEMPT: Bound with {:s}".format(user_dn))
            result = l.search_s(base_dn,ldap.SCOPE_SUBTREE,search_filter)
            l.unbind_s()
            logger.info("AUTH_ATTEMPT: Retrieved {:s}".format(str(result)))
            if len(result) == 1:
                ret = result[0][1] # returns list (search_filter, dict)
                logger.info("AUTH_ATTEMPT: Returning {:s}".format(str(ret)))
            else:
                ret = False
        except ldap.LDAPError as e:
            l.unbind_s()
            logger.error("AUTH_ERROR: Failed {:s} - {:s}".format(username, e))
            ret = False

        if ret:
            logger.info("AUTH_ALLOWED: Authenticated {:s}".format(username))
        else:
            logger.warning("AUTH_DENIED: Denied {:s}".format(username))
            ret = None

        logger.info("AUTH_INFO: Completed auth for {:s}".format(username))
        return ret
