# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

EXTRA_USER_SCHEMA = []

class Authenticator(object):

    def __init__(self):

        # Call Parent
        super(Authenticator, self).__init__()

    def auth_user(self, username, password):
        if username and password:
            return True
        else:
            return False
