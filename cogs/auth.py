# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

### Imports ###

import copy
import os
import hashlib
import uuid

import flask

import backend_redis as backend

import authmod_moodle
import authmod_test


### Constants ###

_USER_SCHEMA = ['username', 'first', 'last', 'auth', 'token']
_GROUP_SCHEMA = ['name']

DEFAULT_AUTHMOD = 'moodle'

SPECIAL_GROUP_ADMIN = '99999999-9999-9999-9999-999999999999'
SPECIAL_GROUP_ANY = '00000000-0000-0000-0000-000000000000'

_GROUP_ADMIN_DICT = {'name': "ADMIN"}

_USERNAMEMAP_KEY = 'username_to_uuid'
_TOKENMAP_KEY = 'token_to_uuid'

_GROUP_LIST_SUFFIX = 'allowedgroups'


### Exceptions ###

class AuthError(Exception):
    """Base class for Auth Exceptions"""

    def __init__(self, *args, **kwargs):
        super(AuthError, self).__init__(*args, **kwargs)

class AuthenticationError(AuthError):
    """Base class for Authentication Exceptions"""

    def __init__(self, *args, **kwargs):
        super(AuthenticationError, self).__init__(*args, **kwargs)

class AuthorizationError(AuthError):
    """Base class for Authorization Exceptions"""

    def __init__(self, *args, **kwargs):
        super(AuthorizationError, self).__init__(*args, **kwargs)

class BadCredentialsError(AuthenticationError):
    """Bad Credentials Exception"""

    def __init__(self, username, *args, **kwargs):
        msg = "Could not authenticate user {:s}".format(username)
        super(BadCredentialsError, self).__init__(msg, *args, **kwargs)

class UserNotAuthorizedError(AuthorizationError):
    """User Not Authorized Exception"""

    def __init__(self, user_uuid, method, path, *args, **kwargs):
        msg = "User {:s} is not authorized to {:s} {:s}".format(user_uuid, method, path_)
        super(UserNotAuthorizedError, self).__init__(msg, *args, **kwargs)


### Classes ###

### Primary Class ###
class Auth(object):

    # Override Constructor
    def __init__(self, db, prefix=None):

        # Call Parent
        super(Auth, self).__init__()

        # Save vars
        self.db = db
        self.prefix = prefix

        # Setup Factories
        passthrough = {'auth': self}
        self.UserFactory = backend.UUIDFactory(UserBase, prefix=self.prefix,
                                               passthrough=passthrough, db=self.db)
        self.GroupFactory = backend.UUIDFactory(GroupBase, prefix=self.prefix,
                                                passthrough=passthrough, db=self.db)
        self.AllowedGroupsFactory = backend.Factory(AllowedGroupsBase, prefix=self.prefix,
                                                    passthrough=passthrough, db=self.db)

        # Setup Lists
        UsernameMapFactory = backend.Factory(UsernameMapBase, prefix=self.prefix,
                                             passthrough=passthrough, db=self.db)
        self.username_map = UsernameMapFactory.from_raw()
        TokenMapFactory = backend.Factory(TokenMapBase, prefix=self.prefix,
                                          passthrough=passthrough, db=self.db)
        self.token_map = TokenMapFactory.from_raw()

        # Setup Admins
        if SPECIAL_GROUP_ADMIN not in self.GroupFactory.list_siblings():
            self.admins = self.GroupFactory.from_custom(SPECIAL_GROUP_ADMIN, _GROUP_ADMIN_DICT)

    # User Methods
    def create_user(self, *args, **kwargs):
        return self.UserFactory.from_new(*args, **kwargs)
    def get_user(self, uuid_hex):
        return self.UserFactory.from_existing(uuid_hex)
    def list_users(self):
        return self.UserFactory.list_siblings()

    # Group Methods
    def create_group(self, data):
        return self.GroupFactory.from_new(data)
    def get_group(self, uuid_hex):
        return self.GroupFactory.from_existing(uuid_hex)
    def list_groups(self):
        return self.GroupFactory.list_siblings()

    # Admin Methods
    def add_admins(self, user_uuids):
        return self.admins.add_users(user_uuids)
    def rem_admins(self, user_uuids):
        return self.admins.rem_users(user_uuids)
    def list_admins(self):
        return self.admins.list_users()

    # Allowed Group Methods
    def add_allowed_groups(self, method, path, group_uuids):
        allowed_groups = self.AllowedGroupsFactory.from_raw(method, path)
        return allowed_groups.add_vals(group_uuids)
    def rem_allowed_groups(self, method, path, group_uuids):
        allowed_groups = self.AllowedGroupsFactory.from_raw(method, path)
        return allowed_groups.del_vals(group_uuids)
    def list_allowed_groups(self, method, path):
        allowed_groups = self.AllowedGroupsFactory.from_raw(method, path)
        return allowed_groups.get_set()

    # Auth Methods
    def auth_token(self, token):
        user_uuid = self.token_map.verify_token(token)
        if user_uuid:
            user = self.srv._get_user(user_uuid)
            return user
        else:
            return False

    def auth_userpass(self, username, password):
        user_uuid = self.username_map.lookup_username(username)
        if user_uuid:
            user = self.get_user(user_uuid)
            auth = self.auth_userpass_mod(username, password, user['auth'])
            if auth:
                return user
            else:
                return False
        else:
            return None

    def auth_userpass_mod(self, username, password, auth_mod):
        if auth_mod == 'moodle':
            authenticator = authmod_moodle.Authenticator()
            moodle_user = authenticator.auth_user(username, password)
            if moodle_user:
                user_data = {}
                user_data['username'] = str(moodle_user.username)
                user_data['first'] = str(moodle_user.first)
                user_data['last'] = str(moodle_user.last)
                user_data['moodle_id'] = str(moodle_user.userid)
                user_data['moodle_token'] = str(moodle_user.token)
                return user_data
            else:
                return False
        elif auth_mod == 'test':
            authenticator = authmod_test.Authenticator()
            test_user = authenticator.auth_user(username, password)
            if test_user:
                user_data = {}
                user_data['username'] = username
                user_data['first'] = 'Test'
                user_data['last'] = 'User'
                return user_data
            else:
                return False
        else:
            raise AuthenticationError("Unknown auth_mod: {:s}".format(auth_mod))

    def get_extra_user_schema(self, auth_mod):
        if auth_mod == 'moodle':
            return authmod_moodle.EXTRA_USER_SCHEMA
        elif auth_mod == 'test':
            return authmod_test.EXTRA_USER_SCHEMA
        else:
            raise Exception("Unknown auth_mod: {:s}".format(auth_mod))

    # Decorators
    def requires_auth_route(self, pass_user=False, pass_owner=False):

        def _decorator(func):

            def _wrapper(*args, **kwargs):

                user = flask.g.user
                path = flask.request.path
                method = flask.request.method
                print("user = {:s}".format(user))
                print("path = {:s}".format(path))
                print("meth = {:s}".format(method))

                user_uuid = str(user.uuid).lower()
                owner_uuid = None

                allowed = False

                # Check if owner
                if owner_uuid:
                    if user_uuid == owner_uuid:
                        allowed = True

                # Check if User is in ADMIN Group
                if not allowed:
                    if user_uuid in self.admins.list_users():
                        allowed = True

                # Setup Group List
                if not allowed:
                    group_uuids = self.list_allowed_groups(method, path)

                # Check if ANY is an Allowed Group
                if not allowed:
                    if SPECIAL_GROUP_ANY in group_uuids:
                        allowed = True

                # Check if User is in an Allowed Group
                if not allowed:
                    for group_uuid in group_uuids:
                        group = self.get_group(group_uuid)
                        if user_uuid in group.list_users():
                            allowed = True
                            break

                # Call Wrapped Function
                if allowed:
                    return func(self, *args, **kwargs)
                else:
                    raise UserNotAuthorizedError(user_uuid, method, path)

            return _wrapper

        return _decorator


## User Account Object ##
class UserBase(backend.TSHashBase):
    """COGS User Class"""

    schema = None

    # Override from_new
    @classmethod
    def from_new(cls, data, username=None, password=None, authmod=None, **kwargs):

        # Check input
        if not username:
            raise TypeError("username required")
        if not password:
            raise TypeError("password required")

        # Dup Data
        data = copy.copy(data)

        # Set Authmod
        if not authmod:
            authmod = auth.DEFAULT_AUTHMOD

        # Confirm user does not exist
        if cls.auth.auth_userpass(username, password) is not None:
            msg = "Username {:s} already exists {:s}".format(username)
            raise backend.ObjectError(msg)

        # Auth User
        user_data = cls.auth.auth_userpass_mod(username, password, authmod)
        if not user_data:
            raise BadCredentialsError(username)
        else:
            data.update(user_data)

        # Seup Remaining Data
        data['auth'] = authmod
        data['token'] = ""

        # Set Schema
        extra_schema = cls.auth.get_extra_user_schema(authmod)
        obj_schema = set(backend.TS_SCHEMA + _USER_SCHEMA + extra_schema)

        # Call Parent
        user = super(UserBase, cls).from_new(data, obj_schema=obj_schema, **kwargs)

        # Setup User Auth
        user_uuid = cls.auth.username_map.map_username(user['username'], str(uuid.UUID(user.obj_key)))
        token = cls.auth.token_map.generate_token(user_uuid)
        user['token'] = token

        # Return Submission
        return user

    # Override from_existing
    @classmethod
    def from_existing(cls, **kwargs):

        # Call Parent
        user = super(UserBase, cls).from_existing(**kwargs)

        # Set Schema
        extra_schema = cls.auth.get_extra_user_schema(user['auth'])
        user.schema = set(backend.TS_SCHEMA + _USER_SCHEMA + extra_schema)

        # Return Submission
        return user

    # Override Delete
    def delete(self):

        # Deallocate User Auth
        self.auth.username_map.rem_username(self['username'])
        self.auth.token_map.rem_token(self['token'])

        # Call Parent
        super(UserBase, self).delete()


## User List Object ##
class UserListBase(backend.SetBase):
    """COGS User List Class"""
    pass


## User Group Object ##
class GroupBase(backend.TSHashBase):
    """COGS Group Class"""

    schema = set(backend.TS_SCHEMA + _GROUP_SCHEMA)

    # Override Constructor
    def __init__(self, uuid_obj):
        """Base Constructor"""

        # Call Parent Construtor
        super(GroupBase, self).__init__(uuid_obj)

        # Setup Lists
        UserListFactory = backend.Factory(UserListBase, prefix=self.full_key, db=self.db)
        self.members = UserListFactory.from_raw('members')

    # Override Delete
    def delete(self):
        if self.members.exists():
            self.members.delete()
        super(GroupBase, self).delete()

    # Members Methods
    def add_users(self, user_uuids):
        return self.members.add_vals(user_uuids)
    def rem_users(self, user_uuids):
        return self.members.del_vals(user_uuids)
    def list_users(self):
        return self.members.get_set()


## Group List Object ##
class GroupListBase(backend.SetBase):
    """COGS Group List Class"""
    pass


## UsernameMap Object ##
class UsernameMapBase(backend.HashBase):

    SCHEMA = None

    # Override and Disable from_new
    @classmethod
    def from_new(cls, *args, **kwargs):
        raise NotImplementedError

    # Override and Disable from_existing
    @classmethod
    def from_existing(cls, *args, **kwargs):
        raise NotImplementedError

    # Override from_raw
    @classmethod
    def from_raw(cls):

        # Set Key
        key = "{:s}".format(_USERNAMEMAP_KEY)

        # Call Parent
        return super(UsernameMapBase, cls).from_raw(key)

    def map_username(self, username, user_uuid):
        self[username.lower()] = user_uuid.lower()
        return self[username.lower()]

    def lookup_username(self, username):
        return self.get(username.lower(), False)

    def rem_username(self, username):
        del(self[username.lower()])


## TokenMap Object ##
class TokenMapBase(backend.HashBase):

    SCHEMA = None

    # Override and Disable from_new
    @classmethod
    def from_new(cls, *args, **kwargs):
        raise NotImplementedError

    # Override and Disable from_existing
    @classmethod
    def from_existing(cls, *args, **kwargs):
        raise NotImplementedError

    # Override from_raw
    @classmethod
    def from_raw(cls):

        # Set Key
        key = "{:s}".format(_TOKENMAP_KEY)

        # Call Parent
        return super(TokenMapBase, cls).from_raw(key)

    def generate_token(self, user_uuid):

        # Generate Token
        rnd = os.urandom(32)
        sha = hashlib.sha256()
        sha.update(rnd)
        token = str(sha.hexdigest()).lower()

        # Set Token
        self[token] = user_uuid.lower()

        # Return Token
        return token

    def verify_token(self, token):
        return self.get(token.lower(), False)

    def rem_token(self, token):
        del(self[token.lower()])


## Allowed Groups Object ##
class AllowedGroupsBase(GroupListBase):

    # Override and Disable from_new
    @classmethod
    def from_new(cls, *args, **kwargs):
        raise NotImplementedError

    # Override and Disable from_existing
    @classmethod
    def from_existing(cls, *args, **kwargs):
        raise NotImplementedError

    # Override from_raw
    @classmethod
    def from_raw(cls, method, path):

        # Set Key
        key = "{:s}_{:s}_{:s}".format(path, method, _GROUP_LIST_SUFFIX)

        # Call Parent
        return super(AllowedGroupsBase, cls).from_raw(key)
