# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import uuid

import redis

_ENCODING = 'utf-8'

_REDIS_HOST = "localhost"
_REDIS_PORT = 6379
_REDIS_DB   = 3

_DUMMY_SCHEMA = ['key1', 'key2', 'key3']
_DUMMY_DIR_KEY = "dummys_list"
_DUMMY_OBJ_KEY = "dummy"

_ASSIGNMENTS_SCHEMA = ['name', 'contact']
_ASSIGNMENTS_DIR_KEY = "assignments_list"
_ASSIGNMENTS_OBJ_KEY = "assignment"

_ASSIGNMENTTESTS_SCHEMA = ['name', 'contact', 'path', 'maxscore']
_ASSIGNMENTTESTS_DIR_KEY = "assignmenttests_list"
_ASSIGNMENTTESTS_OBJ_KEY = "assignmenttest"

### Exceptions

class RedisObjectError(Exception):
    """Base class for Redis Object Exceptions"""

    def __init__(self, *args, **kwargs):
        super(RedisObjectError, self).__init__(*args, **kwargs)

class UUIDRedisObjectError(RedisObjectError):
    """Base class for UUID Redis Object Exceptions"""

    def __init__(self, *args, **kwargs):
        super(UUIDRedisObjectError, self).__init__(*args, **kwargs)

class UUIDRedisObjectDNE(UUIDRedisObjectError):
    """UUID Redis Object Does Not Exist"""

    def __init__(self, obj):
        msg = "{:s} does not exist.".format(obj)
        super(UUIDRedisObjectDNE, self).__init__(msg)

class UUIDRedisObjectMissing(UUIDRedisObjectError):
    """UUID Redis Object Is Missing"""

    def __init__(self, obj):
        msg = "{:s} exists, but is missing.".format(obj)
        super(UUIDRedisObjectMissing, self).__init__(msg)


### Objects

class RedisObject(object):
    """
    Redis Object Base Class

    """

    def __init__(self):
        """Base Constructor"""
        super(RedisObject, self).__init__()
        self.db = redis.StrictRedis(host=_REDIS_HOST, port=_REDIS_PORT, db=_REDIS_DB)


class UUIDRedisObject(RedisObject):
    """
    UUID Redis Object Base Class

    """

    def __init__(self, uuid_obj, parent=None):
        """Base Constructor"""
        super(UUIDRedisObject, self).__init__()
        self.uuid = uuid_obj
        self.schema = _DUMMY_SCHEMA
        self.dir_key = "{:s}".format(_DUMMY_DIR_KEY)
        self.obj_key = "{:s}:{:s}".format(_DUMMY_OBJ_KEY, repr(self))

    @classmethod
    def from_new(cls, d, parent=None):
        """New Constructor"""

        # Create New Object
        uuid_obj = uuid.uuid4()
        obj = cls(uuid_obj, parent)

        # Check dict
        if (set(d.keys()) != set(obj.schema)):
            raise KeyError("Keys {:s} do not match schema {:s}".format(d, obj.schema))

        # Create Atomic Pipeline
        p = obj.db.pipeline(transaction=True)
        # Add Object ID to Set
        p.sadd(obj.dir_key, repr(obj))
        # Add Object Data to DB
        p.hmset(obj.obj_key, d)
        # Execute Pipeline
        if not all(p.execute()):
            raise UUIDRedisObjectError("Create Failed")

        # Return Object
        return obj

    @classmethod
    def from_existing(cls, uuid_hex, parent=None):
        """Existing Constructor"""

        # Create Existing Object
        uuid_obj = uuid.UUID(uuid_hex)
        obj = cls(uuid_obj, parent)

        # Verify Object ID in Set
        if not obj.db.sismember(obj.dir_key, repr(obj)):
            raise UUIDRedisObjectDNE(obj)

        # Return Object
        return obj

    def __unicode__(self):
        u = u"{:s}_{:012x}".format(type(self).__name__, self.uuid.node)
        return u

    def __str__(self):
        s = unicode(self).encode(_ENCODING)
        return s

    def __repr__(self):
        r = "{:s}".format(self.uuid)
        return r

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        return (repr(self) == repr(other))

    def __getitem__(self, k):
        if k in self.schema:
            return self.db.hget(self.obj_key, k)
        else:
            raise KeyError("Key {:s} not valid in {:s}".format(k, self))

    def __setitem__(self, k, v):
        if k in self.schema:
            return self.db.hset(self.obj_key, k, v)
        else:
            raise KeyError("Key {:s} not valid in {:s}".format(k, self))

    def delete(self):
        """Delete"""

        # Create Atomic Pipeline
        p = self.db.pipeline(transaction=True)
        # Delete Object Data from DB
        p.delete(self.obj_key)
        # Remove Object ID from Set
        p.srem(self.dir_key, repr(self))
        # Execute Pipeline
        if not all(p.execute()):
            raise UUIDRedisObjectError("Delete Failed")

    def get_dict(self):
        """Get Dict"""
        d = self.db.hgetall(self.obj_key)
        return d

    def set_dict(self, d):
        """Set Dict"""
        # Check dict
        if (set(d.keys()) != set(self.schema)):
            raise KeyError("Keys {:s} do not match schema {:s}".format(d, self.schema))
        # Set dict
        self.db.hmset(self.obj_key, d)


class Server(RedisObject):
    """
    COGS Server Class

    """

    def __init__(self):
        """Base Constructor"""
        super(Server, self).__init__()

    def list_assignments(self):
        return self.db.smembers(_ASSIGNMENTS_DIR_KEY)


class Assignment(UUIDRedisObject):
    """
    COGS Assignment Class

    """

    def __init__(self, uuid_obj, parent=None):
        """Base Constructor"""

        super(Assignment, self).__init__(uuid_obj)
        self.schema = _ASSIGNMENTS_SCHEMA
        self.dir_key = "{:s}".format(_ASSIGNMENTS_DIR_KEY)
        self.obj_key = "{:s}:{:s}".format(_ASSIGNMENTS_OBJ_KEY, repr(self))

    @classmethod
    def from_new(cls, d):
        """New Constructor"""

        asn = super(Assignment, cls).from_new(d)
        return asn

    @classmethod
    def from_existing(cls, uuid_hex):
        """Existing Constructor"""

        asn = super(Assignment, cls).from_existing(uuid_hex)
        return asn

    def create_test(self, d):
        return AssignmentTest.from_new(d, repr(self))

    def get_test(self, uuid_hex):
        return AssignmentTest.from_existing(uuid_hex, repr(self))

    def list_tests(self):
        dir_key = "{:s}:{:s}".format(_ASSIGNMENTTESTS_DIR_KEY, repr(self))
        return self.db.smembers(dir_key)

class AssignmentTest(UUIDRedisObject):
    """
    COGS Assignment Test Class

    """

    def __init__(self, uuid_obj, parent):
        """Base Constructor"""
        super(AssignmentTest, self).__init__(uuid_obj)
        self.schema = _ASSIGNMENTTESTS_SCHEMA
        self.dir_key = "{:s}:{:s}".format(_ASSIGNMENTTESTS_DIR_KEY, parent)
        self.obj_key = "{:s}:{:s}".format(_ASSIGNMENTTESTS_OBJ_KEY, repr(self))

    @classmethod
    def from_new(cls, d, parent):
        """New Constructor"""

        tst = super(AssignmentTest, cls).from_new(d, parent)
        return tst

    @classmethod
    def from_existing(cls, uuid_hex, parent):
        """Existing Constructor"""

        tst = super(AssignmentTest, cls).from_existing(uuid_hex, parent)
        return tst
