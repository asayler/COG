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

_DUMMY_SCHEMA = []
_DUMMY_DIR_KEY = "dummys"
_DUMMY_OBJ_KEY = _DUMMY_DIR_KEY

_ASSIGNMENTS_SCHEMA = ['name', 'contact']
_ASSIGNMENTS_DIR_KEY = "assignments"
_ASSIGNMENTS_OBJ_KEY = _ASSIGNMENTS_DIR_KEY

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

    def __init__(self, uuid_obj):
        """Base Constructor"""
        super(UUIDRedisObject, self).__init__()
        self.uuid = uuid_obj
        self.schema = _DUMMY_SCHEMA
        self.dir_key = "{:s}".format(_DUMMY_DIR_KEY)
        self.obj_key = "{:s}:{:s}".format(_DUMMY_OBJ_KEY, repr(self))

    @classmethod
    def from_new(cls, d):
        """New Constructor"""

        # Create New Assignment
        uuid_obj = uuid.uuid4()
        asn = cls(uuid_obj)

        # Check dict
        if (set(d.keys()) != set(asn.schema)):
            raise KeyError("Keys {:s} do not match schema {:s}".format(d, asn.schema))

        # Create Atomic Pipeline
        p = asn.db.pipeline(transaction=True)
        # Add Assingment ID to Set
        p.sadd(asn.dir_key, repr(asn))
        # Add Assignment Data to DB
        p.hmset(asn.obj_key, d)
        # Execute Pipeline
        if not all(p.execute()):
            raise UUIDRedisObjectError("Create Failed")

        # Return Assignment
        return asn

    @classmethod
    def from_existing(cls, uuid_hex):
        """Existing Constructor"""

        # Create Existing Assignment
        uuid_obj = uuid.UUID(uuid_hex)
        asn = cls(uuid_obj)

        # Verify Assignment ID in Set
        if not asn.db.sismember(asn.dir_key, repr(asn)):
            raise UUIDRedisObjectDNE(asn)

        # Return Assignment
        return asn

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
        """Delete Assignment"""

        # Create Atomic Pipeline
        p = self.db.pipeline(transaction=True)
        # Delete Assignment Data from DB
        p.delete(self.obj_key)
        # Remove Assingment ID from Set
        p.srem(self.dir_key, repr(self))
        # Execute Pipeline
        if not all(p.execute()):
            raise UUIDRedisObjectError("Delete Failed")

    def get_dict(self):
        """Get Dict from Assignment"""
        d = self.db.hgetall(self.obj_key)
        return d

    def set_dict(self, d):
        """Set Dict for Assignment"""
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

    def assignments_list(self):
        return self.db.smembers(_ASSIGNMENTS_DIR_KEY)


class Assignment(UUIDRedisObject):
    """
    COGS Assignment Class

    """

    def __init__(self, uuid_obj):
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
