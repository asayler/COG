# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


### Imports ###

import copy
import os
import hashlib
import uuid
import functools
import logging

import flask

import backend_redis as backend

import authmod_moodle
import authmod_test
import authmod_ldap

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


### Constants ###

_USER_SCHEMA = ['username', 'first', 'last', 'auth', 'token', 'email']
_GROUP_SCHEMA = ['name']

DEFAULT_AUTHMOD = 'ldap'

SPECIAL_GROUP_ADMIN = '99999999-9999-9999-9999-999999999999'
SPECIAL_GROUP_ANY = '00000000-0000-0000-0000-000000000000'

_GROUP_ADMIN_DICT = {'name': "ADMIN"}

_USERNAMEMAP_KEY = 'username_to_uuid'
_TOKENMAP_KEY = 'token_to_uuid'


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
        msg = "User {:s} is not authorized to {:s} {:s}".format(user_uuid, method, path)
        super(UserNotAuthorizedError, self).__init__(msg, *args, **kwargs)


### Classes ###

### Primary Class ###
class Auth(object):

    # Override Constructor
    def __init__(self, prefix=None):

        # Call Parent
        super(Auth, self).__init__()

        # Save vars
        self.prefix = prefix

        # Setup Factories
        passthrough = {'auth': self}
        self.UserFactory = backend.UUIDFactory(User, prefix=self.prefix, passthrough=passthrough)
        self.GroupFactory = backend.UUIDFactory(Group, prefix=self.prefix, passthrough=passthrough)
        self.AllowedGroupsFactory = backend.PrefixedFactory(AllowedGroups, prefix=self.prefix,
                                                            passthrough=passthrough)

        # Setup Lists
        UsernameMapFactory = backend.PrefixedFactory(UsernameMap, prefix=self.prefix,
                                                     passthrough=passthrough)
        self.username_map = UsernameMapFactory.from_raw()
        TokenMapFactory = backend.PrefixedFactory(TokenMap, prefix=self.prefix,
                                                  passthrough=passthrough)
        self.token_map = TokenMapFactory.from_raw()

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
        if SPECIAL_GROUP_ADMIN not in self.GroupFactory.list_siblings():
            admins = self.GroupFactory.from_custom(SPECIAL_GROUP_ADMIN, _GROUP_ADMIN_DICT)
        else:
            admins = self.GroupFactory.from_existing(SPECIAL_GROUP_ADMIN)
        return admins.add_users(user_uuids)
    def rem_admins(self, user_uuids):
        if SPECIAL_GROUP_ADMIN not in self.GroupFactory.list_siblings():
            admins = self.GroupFactory.from_custom(SPECIAL_GROUP_ADMIN, _GROUP_ADMIN_DICT)
        else:
            admins = self.GroupFactory.from_existing(SPECIAL_GROUP_ADMIN)
        return admins.rem_users(user_uuids)
    def list_admins(self):
        if SPECIAL_GROUP_ADMIN not in self.GroupFactory.list_siblings():
            admins = self.GroupFactory.from_custom(SPECIAL_GROUP_ADMIN, _GROUP_ADMIN_DICT)
        else:
            admins = self.GroupFactory.from_existing(SPECIAL_GROUP_ADMIN)
        return admins.list_users()

    # Allowed Group Methods
    def _allowed_groups_key(self, method, path):
        return "{:s}_{:s}".format(method, path)
    def add_allowed_groups(self, method, path, group_uuids):
        key = self._allowed_groups_key(method, path)
        allowed_groups = self.AllowedGroupsFactory.from_raw(key=key)
        return allowed_groups.add_vals(group_uuids)
    def rem_allowed_groups(self, method, path, group_uuids):
        key = self._allowed_groups_key(method, path)
        allowed_groups = self.AllowedGroupsFactory.from_raw(key=key)
        return allowed_groups.del_vals(group_uuids)
    def list_allowed_groups(self, method, path):
        key = self._allowed_groups_key(method, path)
        allowed_groups = self.AllowedGroupsFactory.from_raw(key=key)
        return allowed_groups.get_set()

    # Auth Methods
    def auth_token(self, token):
        user_uuid = self.token_map.verify_token(token)
        if user_uuid:
            user = self.get_user(user_uuid)
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

        logger.debug("Authenticating {:s} via {:s}".format(username, auth_mod))

        if auth_mod == 'moodle':
            authenticator = authmod_moodle.Authenticator()
            moodle_user = authenticator.auth_user(username, password)
            if moodle_user:
                user_data = {}
                user_data['username'] = str(moodle_user.username)
                user_data['first'] = str(moodle_user.first)
                user_data['last'] = str(moodle_user.last)
                user_data['email'] = str(moodle_user.email)
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
                user_data['email'] = 'test.user@fake.com'
                return user_data
            else:
                return False
	elif auth_mod == 'ldap':
	    authenticator = authmod_ldap.Authenticator()
	    ldap_user = authenticator.auth_user(username, password)
	    if ldap_user:
		    user_data = {}
		    user_data['username'] = str(ldap_user['uid'])
		    user_data['first'] = str(ldap_user['cn']) ## cn contains full name
		    user_data['email'] = str(ldap_user['email'])
		    return user_data
	    else:
		    return False
            raise AuthenticationError("Unknown auth_mod: {:s}".format(auth_mod))

    def get_extra_user_schema(self, auth_mod):
        if auth_mod == 'moodle':
            return authmod_moodle.EXTRA_USER_SCHEMA
	elif auth_mod == 'ldap':
	    return authmod_ldap.EXTRA_USER_SCHEMA
        elif auth_mod == 'test':
            return authmod_test.EXTRA_USER_SCHEMA
        else:
            raise Exception("Unknown auth_mod: {:s}".format(auth_mod))

    # Decorators
    def requires_auth_route(self):

        def _decorator(func):

            @functools.wraps(func)
            def _wrapper(*args, **kwargs):

                user = flask.g.user
                path = flask.request.path
                method = flask.request.method

                user_uuid = str(user.uuid)
                owner_uuid = getattr(flask.g, 'owner', None)

                allowed = False
                auth_info = "{:s} for {:s} at {:s}".format(user['username'], method, path)

                logger.debug("VERIFYING {:s}".format(auth_info))

                # Check if owner
                if owner_uuid:
                    if (user_uuid.lower() == owner_uuid.lower()):
                        logger.debug("ALLOW OWNER {:s}".format(auth_info))
                        allowed = True

                # Check if User is in ADMIN Group
                if not allowed:
                    if user_uuid in self.list_admins():
                        logger.debug("ALLOW ADMIN {:s}".format(auth_info))
                        allowed = True

                # Setup Group List
                if not allowed:
                    group_uuids = self.list_allowed_groups(method, path)

                # Check if ANY is an Allowed Group
                if not allowed:
                    if SPECIAL_GROUP_ANY in group_uuids:
                        logger.debug("ALLOW GROUP_ANY {:s}".format(auth_info))
                        allowed = True

                # Check if User is in an Allowed Group
                if not allowed:
                    for group_uuid in group_uuids:
                        group = self.get_group(group_uuid)
                        if user_uuid in group.list_users():
                            logger.debug("ALLOW GROUP_{:s} {:s}".format(group['name'], auth_info))
                            allowed = True
                            break

                # Call Wrapped Function
                if allowed:
                    return func(*args, **kwargs)
                else:
                    logger.info("DENY {:s}".format(auth_info))
                    raise UserNotAuthorizedError(user_uuid, method, path)

            return _wrapper

        return _decorator


## User Account Object ##
class User(backend.SchemaHash, backend.TSHash, backend.Hash):
    """COGS User Class"""

    # Override from_new
    @classmethod
    def from_new(cls, data, **kwargs):

        username = kwargs.pop('username', None)
        password = kwargs.pop('password', None)
        authmod = kwargs.pop('authmod', None)
        auth = kwargs.get('auth', None)

        # Check input
        if not username:
            raise TypeError("username required")
        if not password:
            raise TypeError("password required")

        # Dup Data
        data = copy.copy(data)

        # Set Authmod
        if not authmod:
            authmod = DEFAULT_AUTHMOD

        # Confirm user does not exist
        if auth.auth_userpass(username, password) is not None:
            msg = "Username {:s} already exists {:s}".format(username)
            raise backend.ObjectError(msg)

        # Auth User
        user_data = auth.auth_userpass_mod(username, password, authmod)
        if not user_data:
            raise BadCredentialsError(username)
        else:
            data.update(user_data)

        # Setup Remaining Data
        data['auth'] = authmod
        data['token'] = ""

        # Set Schema
        schema = set(_USER_SCHEMA)
        schema.update(set(auth.get_extra_user_schema(authmod)))
        kwargs['schema'] = schema

        # Call Parent
        user = super(User, cls).from_new(data, **kwargs)

        # Setup User Auth
        user_uuid = auth.username_map.map_username(user['username'], str(uuid.UUID(user.obj_key)))
        token = auth.token_map.generate_token(user_uuid)
        user['token'] = token

        # Return User
        return user

    # Override Delete
    def delete(self):

        # Deallocate User Auth
        self.auth.username_map.rem_username(self['username'])
        self.auth.token_map.rem_token(self['token'])

        # Call Parent
        super(User, self).delete()


## User List Object ##
class UserList(backend.Set):
    """COGS User List Class"""
    pass


## User Group Object ##
class Group(backend.SchemaHash, backend.TSHash, backend.Hash):
    """COGS Group Class"""

    # Override Constructor
    def __init__(self, *args, **kwargs):
        """Base Constructor"""

        # Call Parent Construtor
        super(Group, self).__init__(*args, **kwargs)

        # Setup Lists
        UserListFactory = backend.PrefixedFactory(UserList, prefix=self.full_key)
        self.members = UserListFactory.from_raw(key='members')

    # Override from_new
    @classmethod
    def from_new(cls, data, **kwargs):

        # Set Schema
        schema = set(_GROUP_SCHEMA)
        kwargs['schema'] = schema

        # Call Parent
        group = super(Group, cls).from_new(data, **kwargs)

        # Return
        return group

    # Override Delete
    def delete(self):
        if self.members.exists():
            self.members.delete()
        super(Group, self).delete()

    # Members Methods
    def add_users(self, user_uuids):
        return self.members.add_vals(user_uuids)
    def rem_users(self, user_uuids):
        return self.members.del_vals(user_uuids)
    def list_users(self):
        return self.members.get_set()


## Group List Object ##
class GroupList(backend.Set):
    """COGS Group List Class"""
    pass


## UsernameMap Object ##
class UsernameMap(backend.Hash):

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
    def from_raw(cls, *args, **kwargs):

        # Set Key
        kwargs['key'] = "{:s}".format(_USERNAMEMAP_KEY)

        # Call Parent
        return super(UsernameMap, cls).from_raw(*args, **kwargs)

    def map_username(self, username, user_uuid):
        self[username.lower()] = user_uuid.lower()
        return self[username.lower()]

    def lookup_username(self, username):
        return self.get(username.lower(), False)

    def rem_username(self, username):
        del(self[username.lower()])


## TokenMap Object ##
class TokenMap(backend.Hash):

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
    def from_raw(cls, *args, **kwargs):

        # Set Key
        kwargs['key'] = "{:s}".format(_TOKENMAP_KEY)

        # Call Parent
        return super(TokenMap, cls).from_raw(*args, **kwargs)

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
class AllowedGroups(GroupList):

    # Override and Disable from_new
    @classmethod
    def from_new(cls, *args, **kwargs):
        raise NotImplementedError

    # Override and Disable from_existing
    @classmethod
    def from_existing(cls, *args, **kwargs):
        raise NotImplementedError
