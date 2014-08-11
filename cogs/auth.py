# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import os
import hashlib
import uuid

import flask

import backend_redis as backend

import authmod_moodle
import authmod_test

_USER_SCHEMA = ['username', 'first', 'last', 'auth', 'token']
_GROUP_SCHEMA = ['name']

DEFAULT_AUTHMOD = 'moodle'

_SPECIAL_GROUP_ADMIN = '99999999-9999-9999-9999-999999999999'
_SPECIAL_GROUP_ANY = '00000000-0000-0000-0000-000000000000'

_GROUP_ADMIN_DICT = {'name': "ADMIN"}

_USERNAMEMAP_KEY = 'username_to_uuid'
_TOKENMAP_KEY = 'token_to_uuid'

_GROUP_LIST_SUFFIX = 'allowedgroups'

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

class BadCredentialsError(AuthorizationError):
    """Bad Credentials Exception"""

    def __init__(self, username, *args, **kwargs):
        msg = "Could not authenticate user {:s}".format(username)
        super(BadCredentialsError, self).__init__(msg, *args, **kwargs)


### Classes ###

class TokensBase(backend.HashBase):
    SCHEMA = None
    pass


class UsernamesBase(backend.HashBase):
    SCHEMA = None
    pass


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
        if cls.auth.auth_user(username, password) is not None:
            msg = "Username {:s} already exists {:s}".format(username)
            raise backend.ObjectError(msg)

        # Auth User
        user_data = cls.auth.auth_user_mod(username, password, authmod)
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
        obj = super(UserBase, cls).from_new(data, obj_schema=obj_schema, **kwargs)

        # Setup User Auth
        token = cls.auth.init_user_auth(obj)
        obj['token'] = token

        # Return Submission
        return obj

    # Override from_existing
    @classmethod
    def from_existing(cls, **kwargs):

        # Call Parent
        obj = super(UserBase, cls).from_existing(**kwargs)

        # Set Schema
        extra_schema = cls.auth.get_extra_user_schema(obj['auth'])
        obj.schema = set(backend.TS_SCHEMA + _USER_SCHEMA + extra_schema)

        # Return Submission
        return obj

    # Override Delete
    def _delete(self):

        # Deallocate User Auth
        self.auth.remove_user_auth(self)

        # Call Parent
        super(UserBase, self)._delete()


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
    def _delete(self):
        if self.members.exists():
            self.members.delete()
        super(GroupBase, self)._delete()

    # Members Methods
    def add_users(self, user_uuids):
        return self.members.add_vals(user_uuids)
    def rem_users(self, user_uuids):
        return self.members.del_vals(user_uuids)
    def list_users(self):
        return self.members.get_set()


class GroupListBase(backend.SetBase):
    """COGS Group List Class"""
    pass


### Mixins ###

class UserMgmtMixin(object):

    def auth_token(self, token):

        user_uuid = self._verify_token(token)
        if user_uuid:
            user = self.srv._get_user(user_uuid)
            return user
        else:
            return False

    def auth_user(self, username, password):

        user_uuid = self._get_useruuid(username)
        if user_uuid:
            user = self.srv._get_user(user_uuid)
            auth = self.auth_user_mod(username, password, user['auth'])
            if auth:
                return user
            else:
                return False
        else:
            return None

    def auth_user_mod(self, username, password, auth_mod):

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
            raise Exception("Unknown auth_mod: {:s}".format(auth_mod))

    def get_extra_user_schema(self, auth_mod):

        if auth_mod == 'moodle':
            return authmod_moodle.EXTRA_USER_SCHEMA
        elif auth_mod == 'test':
            return authmod_test.EXTRA_USER_SCHEMA
        else:
            raise Exception("Unknown auth_mod: {:s}".format(auth_mod))

    def init_user_auth(self, user):

        user_uuid = uuid.UUID(user.obj_key)
        self._set_useruuid(user['username'], str(user_uuid))
        token = self._generate_token(str(user_uuid))
        return token

    def remove_user_auth(self, user):

        self._rem_useruuid(user['username'])
        self._rem_token(user['token'])

    def _set_useruuid(self, username, user_uuid):

        # Process Inputs
        prefix = getattr(self, 'full_key', None)

        # Setup Usernames List
        UsernamesFactory = backend.Factory(UsernamesBase, prefix=prefix, db=self.db)
        usernames = UsernamesFactory.from_raw(_USERNAMEMAP_KEY)

        usernames[username.lower()] = user_uuid.lower()
        return usernames[username.lower()]

    def _get_useruuid(self, username):

        # Process Inputs
        prefix = getattr(self, 'full_key', None)

        # Setup Usernames List
        UsernamesFactory = backend.Factory(UsernamesBase, prefix=prefix, db=self.db)
        usernames = UsernamesFactory.from_raw(_USERNAMEMAP_KEY)

        user_uuid = usernames.get_dict().get(username.lower(), None)
        if user_uuid:
            return user_uuid.lower()
        else:
            return False

    def _rem_useruuid(self, username):

        # Process Inputs
        prefix = getattr(self, 'full_key', None)

        # Setup Usernames List
        UsernamesFactory = backend.Factory(UsernamesBase, prefix=prefix, db=self.db)
        usernames = UsernamesFactory.from_raw(_USERNAMEMAP_KEY)

        # Delete Mapping
        del(usernames[username.lower()])

    def _generate_token(self, user_uuid):

        # Process Inputs
        prefix = getattr(self, 'full_key', None)

        # Setup Token List
        TokensFactory = backend.Factory(TokensBase, prefix=prefix, db=self.db)
        tokens = TokensFactory.from_raw(_TOKENMAP_KEY)

        # Generate Token
        rnd = os.urandom(32)
        sha = hashlib.sha256()
        sha.update(rnd)
        token = str(sha.hexdigest()).lower()

        # Set Token
        tokens[token] = user_uuid.lower()
        return token

    def _verify_token(self, token):

        # Process Inputs
        prefix = getattr(self, 'full_key', None)

        # Setup Group List
        TokensFactory = backend.Factory(TokensBase, prefix=prefix, db=self.db)
        tokens = TokensFactory.from_raw(_TOKENMAP_KEY)

        # Check Token
        user_uuid = tokens.get_dict().get(token.lower(), None)
        if user_uuid:
            return user_uuid.lower()
        else:
            return False

    def _rem_token(self, token):

        # Process Inputs
        prefix = getattr(self, 'full_key', None)

        # Setup Group List
        TokensFactory = backend.Factory(TokensBase, prefix=prefix, db=self.db)
        tokens = TokensFactory.from_raw(_TOKENMAP_KEY)

        # Delete Mapping
        del(tokens[token.lower()])


class AdminMgmtMixin(object):
    """
    Authorization Admin Mix-in Class

    """

    def init_admins(self):
        if _SPECIAL_GROUP_ADMIN not in self.GroupFactory.list_siblings():
            self.admins = self.GroupFactory.from_custom(_SPECIAL_GROUP_ADMIN, _GROUP_ADMIN_DICT)

    def list_admins(self):
        return self.admins.list_users()

    def add_admins(self, user_uuids):
        return self.admins.add_users(user_uuids)

    def rem_admins(self, user_uuids):
        return self.admins.rem_users(user_uuids)


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

class Auth(UserMgmtMixin, AdminMgmtMixin, object):

    # Override Constructor
    def __init__(self, db, prefix=None):

        # Call Parent
        super(Auth, self).__init__()

        # Save vars
        self.db = db
        self.prefix = prefix

        # Setup Factories
        self.UserFactory = backend.UUIDFactory(UserBase, prefix=self.prefix, db=self.db, auth=self)
        self.GroupFactory = backend.UUIDFactory(GroupBase, prefix=self.prefix, db=self.db, auth=self)

        # Setup Admins
        self.init_admins()

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

                # # Setup Group List
                # if not allowed:
                #     GroupListFactory = backend.Factory(GroupListBase, prefix=self.prefix, db=self.db)
                #     group_list_key = "{:s}_{:s}_{:s}".format(path, method, _GROUP_LIST_SUFFIX)
                #     group_uuids = GroupListFactory.from_raw(group_list_key).get_set()

                # # Check if ANY is an Allowed Group
                # if not allowed:
                #     if _SPECIAL_GROUP_ANY in group_uuids:
                #         allowed = True

                # # Check if User is in an Allowed Group
                # if not allowed:
                #     for group_uuid in group_uuids:
                #         group = self.srv._get_group(group_uuid)
                #         if user_uuid in group._list_users():
                #             allowed = True
                #             break

                # # Call Wrapped Function
                # if allowed:
                #     return func(self, *args, **kwargs)
                # else:
                #     raise UserNotAuthorizedError(user_uuid, func)

                return func(*args, **kwargs)

            return _wrapper

        return _decorator


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
