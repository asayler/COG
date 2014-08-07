# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


import backend_redis as backend


_SPECIAL_GROUP_ADMIN = '99999999-9999-9999-9999-999999999999'
_SPECIAL_GROUP_ANY = '00000000-0000-0000-0000-000000000000'


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

class GroupListBase(backend.SetBase):
    """
    COGS Group List Class

    """

    pass


### Mixins ###

class AuthorizationAdminMixin(object):
    """
    Authorization Admin Mix-in Class

    """

    def list_admins(self):
        admin_grp = self.srv.GroupFactory.from_raw(_SPECIAL_GROUP_ADMIN)
        return admin_grp._list_users()

    def add_admins(self, user_uuids):
        admin_grp = self.srv.GroupFactory.from_raw(_SPECIAL_GROUP_ADMIN)
        return admin_grp._add_users(user_uuids)

    def rem_admins(self, user_uuids):
        admin_grp = self.srv.GroupFactory.from_raw(_SPECIAL_GROUP_ADMIN)
        return admin_grp._rem_users(user_uuids)


class AuthorizationMgmtMixin(object):
    """
    Authorization Managment Mix-in Class

    """

    def allowed_groups_add(self, func, group_uuids):

        # Process Inputs
        prefix = getattr(self, 'full_key', None)

        # Setup Group List
        sf = backend.Factory(GroupListBase, prefix=prefix, db=self.db)
        groups = sf.from_raw("{:s}_{:s}".format(func.__name__, 'groups'))

        # Add UUIDs to Group List
        return groups.add_vals(groups_uuids)

    def allowed_groups_rem(self, func, group_uuids):

        # Process Inputs
        prefix = getattr(self, 'full_key', None)

        # Setup Group List
        sf = backend.Factory(GroupListBase, prefix=prefix, db=self.db)
        groups = sf.from_raw("{:s}_{:s}".format(func.__name__, 'groups'))

        # Remove UUIDs from Group List
        return groups.del_vals(groups_uuids)

    def allowed_groups_list(self, func):

        # Process Inputs
        prefix = getattr(self, 'full_key', None)

        # Setup Group List
        sf = backend.Factory(GroupListBase, prefix=prefix, db=self.db)
        groups = sf.from_raw("{:s}_{:s}".format(func.__name__, 'groups'))

        # Return Group List
        return groups.get_set()


###  Decorators ###

def requires_authorization(func):

    def _wrapper(self, *args, **kwargs):

        # Extract Inputs
        user_uuid = kwargs.pop('user', None)
        prefix = getattr(self, 'full_key', None)
        allowed = False

        # Setup Group List
        sf = backend.Factory(GroupListBase, prefix=prefix, db=self.db)
        group_uuids = sf.from_raw("{:s}_{:s}".format(func.__name__, 'groups')).get_set()

        # Check if User is in ADMIN Group
        if not allowed:
            print("groups = {:s}".format(self.srv._list_groups()))
            if _SPECIAL_GROUP_ADMIN in self.srv._list_groups():
                print("Admin Group Detected")
                if user_uuid in self.srv._get_group(_SPECIAL_GROUP_ADMIN):
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
        return func(self, *args, **kwargs)
        # if allowed:
        #     return func(self, *args, **kwargs)
        # else:
        #     raise UserNotAuthorizedError(user_uuid, func)

    return _wrapper
