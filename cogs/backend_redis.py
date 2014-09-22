# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


import copy
import os
import collections

import redis

import config
import backend
from backend import BackendError, FactoryError, PersistentObjectError, ObjectDNE


TS_SCHEMA = ['created_time', 'modified_time']

db = redis.StrictRedis(host=config.REDIS_HOST,
                       port=config.REDIS_PORT,
                       db=config.REDIS_DB,
                       password=config.REDIS_PASSWORD)


### Redis Factories ###

class PrefixedFactory(backend.PrefixedFactory):
    """
    Prefix Object Factory

    """

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


class UUIDFactory(backend.UUIDFactory, PrefixedFactory):
    """
    UUID Object Factory

    """
    pass


### Redis Base Objects ###

class TypedObject(backend.TypedObject):
    """
    Typed Redis Object Class

    """

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


### Redis Set Objects ###

class Set(backend.Set, TypedObject):
    """
    Redis Set Object Class

    """

    @classmethod
    def from_new(cls, vals, **kwargs):
        """New Constructor"""

        # Check Input
        if not ((type(vals) == list) or (type(vals) == set)):
            raise TypeError("Vals must be a list or set")
        if not vals:
            raise ValueError("Input must not be empty")

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
        """Check if Val in Set"""

        return db.sismember(self.full_key, val)

    def add(self, val):
        """Add Val to Set"""

        return db.sadd(self.full_key, val)

    def discard(self, val):
        """Remove Val from Set"""

        return db.srem(self.full_key, val)

    def get_set(self):
        """Get Static Set from Object"""

        return db.smembers(self.full_key)

    def add_vals(self, vals):
        """Add Vals to Set"""

        # Check Input
        if not ((type(vals) == list) or (type(vals) == set)):
            raise TypeError("Vals must be a list or set")
        if not vals:
            raise ValueError("Input must not be empty")

        return db.sadd(self.full_key, *vals)

    def del_vals(self, vals):
        """Remove Vals from Set"""

        # Check Input
        if not ((type(vals) == list) or (type(vals) == set)):
            raise TypeError("Vals must be a list or set")
        if not vals:
            raise ValueError("Input must not be empty")

        return db.srem(self.full_key, *vals)


### Redis Hash Objects ###

class Hash(backend.Hash, TypedObject):
    """
    Redis Hash Object Class

    """

    @classmethod
    def from_new(cls, data, **kwargs):
        """New Constructor"""

        # Check Input
        if (type(data) != dict):
            raise TypeError("Data must be a list or set")
        if not data:
            raise ValueError("Input must not be empty")

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

    def __getitem__(self, key):
        """Get Dict Item"""
        ret = db.hget(self.full_key, key)
        return ret

    def __setitem__(self, key, val):
        """Set Dict Item"""
        ret = db.hset(self.full_key, key, val)
        return ret

    def __delitem__(self, key):
        """Delete Dict Item"""
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

    def set_dict(self, data):
        """Set Full Dict"""

        # Check Input
        if (type(data) != dict):
            raise TypeError("Data must be a list or set")
        if not data:
            raise ValueError("Input must not be empty")

        # Update Object
        ret = db.hmset(self.full_key, data)
        if not ret:
            raise PersistentObjectError("Set Failed")


class TSHash(backend.TSHash, Hash):
    """
    Redis Time-Stamped Hash Object Class

    """
    pass


class OwnedHash(backend.OwnedHash, Hash):
    """
    Redis Owned Hash Object Class

    """
    pass


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
        hsh.schema.add_vals(schema)
        return hsh

    def __setitem__(self, key, val):
        """Set Dict Item"""
        if key in self.schema:
            return super(SchemaHash, self).__setitem__(key, val)
        else:
            msg = "{:s} not in {:s}".format(key, self.schema)
            raise KeyError(msg)

    def __delitem__(self, key):
        """Del Dict Item"""

        if key in self.schema:
            return super(SchemaHash, self).__delitem__(key)
        else:
            msg = "{:s} not in {:s}".format(key, self.schema)
            raise KeyError(msg)

    def set_dict(self, data):
        """Set Full Dict"""

        schema = self.schema.get_set()

        keys = set(data.keys())
        if not (keys <= schema):
            msg = "{:s} do not match {:s}".format(keys, schema)
            raise KeyError(msg)

        return super(SchemaHash, self).set_dict(data)

    def delete(self):
        """ Delete Object"""

        # Delete Schema Set
        self.schema.delete()

        # Call Parent
        super(SchemaHash, self).delete()
