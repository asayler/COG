# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

# pylint: disable=no-member

import copy
import time
import uuid
import collections
import os

import redis

import config
import backend
from backend import BackendError, FactoryError, PersistentObjectError, ObjectDNE


TS_SCHEMA = ['created_time', 'modified_time']

db = redis.StrictRedis(host=config.REDIS_HOST,
                       port=config.REDIS_PORT,
                       db=config.REDIS_DB,
                       password=config.REDIS_PASSWORD)


### Objects ###

class TypedObject(backend.TypedObject):

    @classmethod
    def from_new(cls, *args, **kwargs):
        """New Constructor"""

        obj = super(TypedObject, cls).from_new(*args, **kwargs)
        if db.exists(obj.key):
            raise PersistentObjectError("Key already exists in DB")
        return obj

    @classmethod
    def from_existing(cls, *args, **kwargs):
        """Existing Constructor"""

        obj = super(TypedObject, cls).from_existing(*args, **kwargs)
        if not db.exists(obj.key):
            raise ObjectDNE(obj)
        return obj

    def delete(self):
        """Delete Object"""

        if not db.delete(self.key):
            raise PersistentObjectError("Delete Failed")
        super(TypedObject, self).delete()

    def exists(self):
        """Check if object exists"""

        return db.exists(self.full_key)


class PrefixedFactory(backend.PrefixedFactory):

    def list_family(self):
        """List Factory Objects"""
        if self.prefix:
            pre_key = "{:s}{:s}".format(self.prefix, backend._FIELD_SEP).lower()
        else:
            pre_key = ""
        query = "{:s}*".format(pre_key)
        fam_lst = db.keys(query)
        obj_keys = set([])
        for itm in fam_lst:
            full_key = itm[len(pre_key): ]
            if self.typed:
                typ_key = full_key[0:full_key.find(backend._TYPE_SEP)]
                obj_key = full_key[(len(typ_key) + 1): ]
                if typ_key == self.cls_name:
                    obj_keys.add(obj_key)
            else:
                obj_keys.add(full_key)
        return obj_keys


class UUIDFactory(PrefixedFactory):

    def from_new(self, *args, **kwargs):
        obj_uuid = uuid.uuid4()
        kwargs['uuid'] = obj_uuid
        kwargs['key'] = str(obj_uuid)
        return super(UUIDFactory, self).from_new(*args, **kwargs)

    def from_custom(self, uuid_str, *args, **kwargs):
        obj_uuid = uuid.UUID(str(uuid_str))
        kwargs['uuid'] = obj_uuid
        kwargs['key'] = str(obj_uuid)
        return super(UUIDFactory, self).from_new(*args, **kwargs)

    def from_existing(self, uuid_str, *args, **kwargs):
        obj_uuid = uuid.UUID(str(uuid_str))
        kwargs['uuid'] = obj_uuid
        kwargs['key'] = str(obj_uuid)
        return super(UUIDFactory, self).from_existing(*args, **kwargs)

    def from_raw(self, uuid_str, *args, **kwargs):
        obj_uuid = uuid.UUID(str(uuid_str))
        kwargs['uuid'] = obj_uuid
        kwargs['key'] = str(obj_uuid)
        return super(UUIDFactory, self).from_raw(*args, **kwargs)


class Hash(collections.MutableMapping, TypedObject):
    """
    Redis Hash  Class

    """

    @classmethod
    def from_new(cls, data, **kwargs):
        """New Constructor"""

        # Check Input
        if not data:
            raise PersistentObjectError("Input dict must not be None or empty")

        # Call Parent
        obj = super(Hash, cls).from_new(**kwargs)

        # Add Object Data to DB
        if not db.hmset(obj.full_key, data):
            raise PersistentObjectError("Create Failed")

        # Return Object
        return obj

    def __len__(self):
        """Get Len of Hash"""
        ret = db.hlen(self.full_key)
        return ret

    def __iter__(self):
        """Iterate Keys"""
        for key in db.hkeys(self.full_key):
            yield key

    def __getitem__(self, k):
        """Get Dict Item"""
        ret = db.hget(self.full_key, k)
        return ret

    def __setitem__(self, k, v):
        """Set Dict Item"""
        ret = db.hset(self.full_key, k, v)
        return ret

    def __delitem__(self, key):
        ret = db.hdel(self.full_key, key)
        return ret

    def keys(self):
        """Get Dict Keys"""
        ret = db.hkeys(self.full_key)
        return ret

    def get_dict(self):
        """Get Full Dict"""
        ret = db.hgetall(self.full_key)
        return ret

    def set_dict(self, d):
        """Set Full Dict"""
        if not d:
            raise PersistentObjectError("Input dict must not be None or empty")
        ret = db.hmset(self.full_key, d)
        if not ret:
            raise PersistentObjectError("Set Failed")


class TSHash(Hash):
    """
    Time-stamped Hash  Class
    """

    @classmethod
    def from_new(cls, data, **kwargs):
        """New Constructor"""

        # Set Times
        data = copy.copy(data)
        t = str(time.time())
        data['created_time'] = t
        data['modified_time'] = t

        # Call Parent
        obj = super(TSHash, cls).from_new(data, **kwargs)

        # Return Object
        return obj

    def __setitem__(self, k, v):
        """Set Item"""

        # Set Time
        data = {}
        data['modified_time'] = str(time.time())

        # Set Value
        data[k] = v

        # Call Parent
        ret = super(TSHash, self).set_dict(data)

        # Return
        return ret

    def set_dict(self, d):
        """Set Dict"""

        # Set Time
        data = copy.deepcopy(d)
        data['modified_time'] = str(time.time())

        # Call Parent
        ret = super(TSHash, self).set_dict(data)

        # Return
        return ret


class OwnedHash(Hash):
    """
    Owned and Time-stamped Hash  Class
    """

    @classmethod
    def from_new(cls, data, **kwargs):
        """New Constructor"""

        owner = kwargs.pop('owner', None)
        if not owner:
            raise TypeError("Requires 'owner'")

        # Set Owner
        data = copy.copy(data)
        data['owner'] = str(owner.uuid).lower()

        # Call Parent
        obj = super(OwnedHash, cls).from_new(data, **kwargs)

        # Return Run
        return obj


class Set(collections.MutableSet, TypedObject):
    """
    Redis Set  Class

    """

    @classmethod
    def from_new(cls, vals, **kwargs):
        """New Constructor"""

        # Check Input
        if not vals:
            raise PersistentObjectError("Input set must not be None or empty")

        # Call Parent
        obj = super(Set, cls).from_new(**kwargs)

        # Add lst to DB
        if not db.sadd(obj.full_key, *vals):
            raise PersistentObjectError("Create Failed")

        # Return Object
        return obj

    def __len__(self):
        """Get Len of Set"""

        return len(db.smembers(self.full_key))

    def __iter__(self):
        """Iterate Values"""

        for val in db.smembers(self.full_key):
            yield val

    def __contains__(self, val):

        return db.sismember(self.full_key, val)

    def add(self, val):

        return db.sadd(self.full_key, val)

    def discard(self, val):

        return db.srem(self.full_key, val)

    def get_set(self):
        """Get All Vals from Set"""

        return db.smembers(self.full_key)

    def add_vals(self, vals):
        """Add Vals to Set"""

        return db.sadd(self.full_key, *vals)

    def del_vals(self, vals):
        """Remove Vals from Set"""

        return db.srem(self.full_key, *vals)


class Schema(Set):
    pass


class SchemaHash(Hash):

    def __init__(self, *args, **kwargs):

        super(SchemaHash, self).__init__(*args, **kwargs)

        SchemaFactory = PrefixedFactory(Schema, prefix=self.full_key)
        self.schema = SchemaFactory.from_raw()

    @classmethod
    def from_new(cls, data, **kwargs):

        schema = kwargs.pop('schema', None)
        if not schema:
            raise TypeError("Requires 'schema'")
        schema = set(schema)

        keys = set(data.keys())
        if (keys != schema):
            msg = "{:s} do not match {:s}".format(keys, schema)
            raise KeyError(msg)

        hsh = super(SchemaHash, cls).from_new(data, **kwargs)
        hsh.schema.add_vals(keys)
        return hsh

    def __setitem__(self, key, val):
        """Set Dict Item"""
        if key in self.schema:
            return super(SchemaHash, self).__setitem__(key, val)
        else:
            msg = "{:s} not in {:s}".format(key, schema)
            raise KeyError(msg)

    def __delitem__(self, key):
        """Del Dict Item"""

        if key in self.schema:
            return super(SchemaHash, self).__delitem__(key)
        else:
            msg = "{:s} not in {:s}".format(key, schema)
            raise KeyError(msg)

    def set_dict(self, d):
        """Set Full Dict"""
        raise NotImplementedError("set_dict not allowed on SchemaHash")
