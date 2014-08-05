# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import backend_redis as backend


_BASE_SCHEMA = ['created_time', 'modified_time']
_USER_SCHEMA = ['username', 'first', 'last', 'type']
_GROUP_SCHEMA = ['name', 'members']
_COL_PERMISSION_SCHEMA = ['create', 'list']
_OBJ_PERMISSION_SCHEMA = ['read', 'write', 'delete']
_ASSIGNMENTS_SCHEMA = ['name', 'contact', 'permissions']
_TESTS_SCHEMA = ['name', 'contact', 'type', 'maxscore']
_SUBMISSIONS_SCHEMA = ['author']
_RUNS_SCHEMA = ['test', 'status', 'score', 'output']
_FILES_SCHEMA = ['key', 'name', 'type', 'encoding', 'path']

_FILES_DIR = "./files/"


### COGS Core Objects ###

class Server(object):
    """
    COGS Server Class

    """

    # Override Constructor
    def __init__(self, db=None):
        """Base Constructor"""

        # Call Parent Construtor
        super(Server, self).__init__()

        # Setup Factories
        self.AssignmentFactory = backend.UUIDFactory(AssignmentBase, db=db)
        self.UserFactory = backend.UUIDFactory(UserBase, db=db)

    # Assignment Methods
    def create_assignment(self, d):
        return self.AssignmentFactory.from_new(d)
    def get_assignment(self, uuid_hex):
        return self.AssignmentFactory.from_existing(uuid_hex)
    def get_assignments(self):
        return self.AssignmentFactory.get_siblings()
    def list_assignments(self):
        return self.AssignmentFactory.list_siblings()

    # User Methods
    def create_user(self, d):
        return self.UserFactory.from_new(d)
    def get_user(self, uuid_hex):
        return self.UserFactory.from_existing(uuid_hex)
    def get_users(self):
        return self.UserFactory.get_siblings()
    def list_users(self):
        return self.UserFactory.list_siblings()


### COGS Base Objects ###
