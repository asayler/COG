# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


import os
import hashlib

import backend_redis as backend

_SPECIAL_GROUP_ADMIN = '99999999-9999-9999-9999-999999999999'
_SPECIAL_GROUP_ANY = '00000000-0000-0000-0000-000000000000'

_GROUP_ADMIN_DICT = {'name': "ADMIN"}

### Exceptions ###

class AuthorizationError(Exception):
    """Base class for Authorization Exceptions"""

    def __init__(self, *args, **kwargs):
        super(AuthorizationError, self).__init__(*args, **kwargs)

class UserNotAuthorizedError(AuthorizationError):
    """User Not Authorized Exception"""

    def __init__(self, user_uuid, func, *args, **kwargs):
        msg = "User '{:s}' is not authorized to access '{:s}'".format(user_uuid, func.__name__)
        super(UserNotAuthorizedError, self).__init__(msg, *args, **kwargs)


### Classes ###

class UserTokensBase(backend.HashBase):

    SCHEMA = None

    pass

class UserNamesBase(backend.HashBase):

    SCHEMA = None

    pass

class GroupListBase(backend.SetBase):
    """
    COGS Group List Class

    """

    pass


### Mixins ###

class UserMgmtMixin(object):

    def set_useruuid(self, username, user_uuid):

        # Process Inputs
        prefix = getattr(self, 'full_key', None)

        # Setup Usernames List
        UserNamesFactory = backend.Factory(UserNamesBase, prefix=prefix, db=self.db)
        usernames = UserNamesFactory.from_raw('usernames')

        usernames[str(username).lower()] = str(usr_uuid).lower()
        return usernames[str(username).lower()]

    def get_useruuid(self, username):

        # Process Inputs
        prefix = getattr(self, 'full_key', None)

        # Setup Usernames List
        UserNamesFactory = backend.Factory(UserNamesBase, prefix=prefix, db=self.db)
        usernames = UserNamesFactory.from_raw('usernames')

        user_uuid = usernames.get_dict().get(str(username).lower(), None)
        return str(user_uuid).lower()

    def generate_token(self, user_uuid):

        # Process Inputs
        prefix = getattr(self, 'full_key', None)

        # Setup Token List
        UserTokensFactory = backend.Factory(UserTokensBase, prefix=prefix, db=self.db)
        tokens = UserTokensFactory.from_raw('tokens')

        # Generate Token
        rnd = os.urandom(32)
        sha = hashlib.sha256()
        sha.update(rnd)
        token = str(sha.hexdigest()).lower()

        # Set Token
        tokens[str(user_uuid).lower()] = token
        return token

    def verify_token(self, token):

        # Process Inputs
        prefix = getattr(self, 'full_key', None)

        # Setup Group List
        UserTokensFactory = backend.Factory(UserTokensBase, prefix=prefix, db=self.db)
        tokens = UserTokensFactory.from_raw('tokens')

        # Check Token
        user_uuid = tokens.get_dict().get(str(token).lower(), None)
        return str(user_uuid).lower()


class AuthorizationAdminMixin(object):
    """
    Authorization Admin Mix-in Class

    """

    def init_admins(self):
        if _SPECIAL_GROUP_ADMIN not in self.srv.GroupFactory.list_siblings():
            self.admins = self.srv.GroupFactory.from_custom(_SPECIAL_GROUP_ADMIN, _GROUP_ADMIN_DICT)

    def list_admins(self):
        return self.srv.admins._list_users()

    def add_admins(self, user_uuids):
        return self.srv.admins._add_users(user_uuids)

    def rem_admins(self, user_uuids):
        return self.srv.admins._rem_users(user_uuids)


class AuthorizationMgmtMixin(object):
    """
    Authorization Managment Mix-in Class

    """

    def allowed_groups_add(self, func, group_uuids):

        # Process Inputs
        prefix = getattr(self, 'full_key', None)

        # Setup Group List
        GroupListFactory = backend.Factory(GroupListBase, prefix=prefix, db=self.db)
        groups = GroupListFactory.from_raw("{:s}_{:s}".format(func.__name__, 'groups'))

        # Add UUIDs to Group List
        return groups.add_vals(groups_uuids)

    def allowed_groups_rem(self, func, group_uuids):

        # Process Inputs
        prefix = getattr(self, 'full_key', None)

        # Setup Group List
        GroupListFactory = backend.Factory(GroupListBase, prefix=prefix, db=self.db)
        groups = GroupListFactory.from_raw("{:s}_{:s}".format(func.__name__, 'groups'))

        # Remove UUIDs from Group List
        return groups.del_vals(groups_uuids)

    def allowed_groups_list(self, func):

        # Process Inputs
        prefix = getattr(self, 'full_key', None)

        # Setup Group List
        GroupListFactory = backend.Factory(GroupListBase, prefix=prefix, db=self.db)
        groups = GroupListFactory.from_raw("{:s}_{:s}".format(func.__name__, 'groups'))

        # Return Group List
        return groups.get_set()


###  Decorators ###

def requires_authorization(pass_user=False, pass_owner=False):

    def _decorator(func):

        def _wrapper(self, *args, **kwargs):

            # Extract Inputs
            if pass_user:
                user = kwargs.get('user', None)
            else:
                user = kwargs.pop('user', None)
            if pass_owner:
                owner = kwargs.get('owner', None)
            else:
                owner = kwargs.pop('owner', None)

            if user:
                user_uuid = str(user.uuid).lower()
            else:
                user_uuid = None
            if owner:
                owner_uuid = str(owner.uuid).lower()
            else:
                owner_uuid = None
            prefix = getattr(self, 'full_key', None)
            allowed = False

            # Check if owner
            if owner_uuid:
                if user_uuid == owner_uuid:
                    allowed = True

            # Setup Group List
            if not allowed:
                sf = backend.Factory(GroupListBase, prefix=prefix, db=self.db)
                group_uuids = sf.from_raw("{:s}_{:s}".format(func.__name__, 'groups')).get_set()

            # Check if User is in ADMIN Group
            if not allowed:
                if _SPECIAL_GROUP_ADMIN in self.srv._list_groups():
                    admins = self.srv._get_group(_SPECIAL_GROUP_ADMIN)
                    if user_uuid in admins._list_users():
                        allowed = True

            # Check if ANY is an Allowed Group
            if not allowed:
                if _SPECIAL_GROUP_ANY in group_uuids:
                    allowed = True

            # Check if User is in an Allowed Group
            if not allowed:
                for group_uuid in group_uuids:
                    group = self.srv._get_group(group_uuid)
                    if user_uuid in group._list_users():
                        allowed = True
                        break

            # Call Wrapped Function
            if allowed:
                return func(self, *args, **kwargs)
            else:
                raise UserNotAuthorizedError(user_uuid, func)

        return _wrapper

    return _decorator
