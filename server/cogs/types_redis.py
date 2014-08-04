# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import copy

import redis

_ENCODING = 'utf-8'
_SUF_BASE = 'Base'
_FIELD_SEP = ':'
_TYPE_SEP = '+'
assert(_FIELD_SEP != _TYPE_SEP)
_REDIS_CONF_DEFAULT = {'redis_host': "localhost",
                       'redis_port': 6379,
                       'redis_db': 4}

### Exceptions

class DatatypesError(Exception):
    """Base class for Datatypes Exceptions"""

    def __init__(self, *args, **kwargs):
        super(DatatypesError, self).__init__(*args, **kwargs)

class RedisFactoryError(DatatypesError):
    """Base class for Redis Factory Exceptions"""

    def __init__(self, *args, **kwargs):
        super(RedisFactoryError, self).__init__(*args, **kwargs)

class RedisObjectError(DatatypesError):
    """Base class for Redis Object Exceptions"""

    def __init__(self, *args, **kwargs):
        super(RedisObjectError, self).__init__(*args, **kwargs)

class RedisObjectDNE(RedisObjectError):
    """ Redis Object Does Not Exist"""

    def __init__(self, obj):
        msg = "{:s} does not exist.".format(obj)
        super(RedisObjectDNE, self).__init__(msg)


### Objects

class RedisObjectBase(object):

    @classmethod
    def from_new(cls, key=None):
        """New Constructor"""

        obj = cls(key)
        if obj.db.exists(obj.full_key):
            raise RedisObjectError("Key already exists in DB")
        return obj

    @classmethod
    def from_existing(cls, key):
        """Existing Constructor"""

        obj = cls(key)
        if not obj.db.exists(obj.full_key):
            raise RedisObjectDNE(obj)
        return obj

    def __init__(self, key=None):
        """Base Constructor"""

        super(RedisObjectBase, self).__init__()

        if key:
            if _FIELD_SEP in key:
                raise RedisObjectError("Key may not contain '{:s}'".format(_FIELD_SEP))
            if _TYPE_SEP in key:
                raise RedisObjectError("Key may not contain '{:s}'".format(_TYPE_SEP))

        self.obj_key = key
        self.obj_rid = str(self)

        if self.pre_key and self.obj_key:
            self.full_key = "{:s}{:s}{:s}".format(self.pre_key, _FIELD_SEP, self.obj_rid).lower()
        elif self.pre_key:
            self.full_key = "{:s}".format(self.pre_key).lower()
        elif self.obj_key:
            self.full_key = "{:s}".format(self.obj_rid).lower()
        else:
            raise RedisObjectError("Either pre_key or full_key required")

    def __unicode__(self):
        """Return Unicode Representation"""

        u = u"{:s}".format(type(self).__name__)
        if self.obj_key:
            u += u"{:s}{:s}".format(_TYPE_SEP, self.obj_key)
        return u

    def __str__(self):
        """Return String Representation"""

        s = unicode(self).encode(_ENCODING)
        return s

    def __repr__(self):
        """Return Unique Representation"""

        r = "{:s}".format(self.full_key)
        return r

    def __hash__(self):
        """Return Hash"""

        return hash(repr(self))

    def __eq__(self, other):
        """Test Equality"""

        return (repr(self) == repr(other))

    def delete(self):
        """Delete Object"""

        if not self.db.delete(self.full_key):
            raise RedisObjectError("Delete Failed")


class RedisFactory(object):

    def __init__(self, base_cls, prefix=None, redis_db=None):

        # Call Super
        super(RedisFactory, self).__init__()

        # Check Input
        if not issubclass(base_cls, RedisObjectBase):
            raise RedisFactoryError("cls must be subclass of RedisObjectBase")
        base_name = base_cls.__name__
        if not base_name.endswith(_SUF_BASE):
            raise RedisFactoryError("cls name must end with '{:s}'".format(_SUF_BASE))

        # Setup Class Name
        cls_name = base_name[0:base_name.rfind(_SUF_BASE)]

        # Setup DB
        if redis_db is None:
            self.db = redis.StrictRedis(host=_REDIS_CONF_DEFAULT['redis_host'],
                                        port=_REDIS_CONF_DEFAULT['redis_port'],
                                        db=_REDIS_CONF_DEFAULT['redis_db'])
        else:
            self.db = redis_db

        # Setup Base Key
        if prefix == None:
            self.pre_key = None
        else:
            self.pre_key = prefix

        # Setup Class
        class cls(base_cls):

            pre_key = self.pre_key
            db = self.db

        cls.__name__ = cls_name
        self.cls = cls

    def list_family(self):
        """List Factory Objects"""
        if self.pre_key:
            p = "{:s}{:s}".format(self.pre_key, _FIELD_SEP)
        else:
            p = ""
        q = "{:s}*".format(p)
        fam_lst = self.db.keys(q)
        fam_keys = set([])
        for full_key in fam_lst:
            fam_id = full_key[len(p): ]
            fam_key = fam_id[(fam_id.find(_TYPE_SEP) + 1): ]
            fam_keys.add(fam_key)
        return fam_keys

    def list_siblings(self):
        """List Factory Objects"""
        fam_keys = self.list_family()
        sib_keys = set([])
        for fam_key in fam_keys:
            if _FIELD_SEP not in fam_key:
                sib_keys.add(fam_key)
        return sib_keys

    def list_children(self):
        """List Factory Objects"""
        fam_keys = self.list_family()
        chd_keys = set([])
        for fam_key in fam_keys:
            if _FIELD_SEP in fam_key:
                chd_keys.add(fam_key)
        return chd_keys

    def from_new(self, *args, **kwargs):
        return self.cls.from_new(*args, **kwargs)

    def from_existing(self, *args, **kwargs):
        return self.cls.from_existing(*args, **kwargs)


class RedisHashBase(RedisObjectBase):
    """
    Redis Hash Base Class

    """

    schema = None

    @classmethod
    def from_new(cls, d, key=None):
        """New Constructor"""

        # Check Input
        if not d:
            raise RedisObjectError("Input dict must not be None or empty")

        # Call Parent
        obj = super(RedisHashBase, cls).from_new(key)

        # Check dict
        if obj.schema:
            s = set(d.keys())
            if (s != obj.schema):
                raise KeyError("Keys {:s} do not match schema {:s}".format(s, obj.schema))

        # Add Object Data to DB
        if not obj.db.hmset(obj.full_key, d):
            raise RedisObjectError("Create Failed")

        # Return Object
        return obj

    def __getitem__(self, k):
        """Get Dict Item"""

        if self.schema is not None:
            if k not in self.schema:
                raise KeyError("Key {:s} not valid in {:s}".format(k, self))

        ret = self.db.hget(self.full_key, k)
        if not ret:
            raise KeyError("Key {:s} not found in {:s}".format(k, self))

        return ret

    def __setitem__(self, k, v):
        """Set Dict Item"""

        if self.schema is not None:
            if k not in self.schema:
                raise KeyError("Key {:s} not valid in {:s}".format(k, self))

        ret = self.db.hset(self.full_key, k, v)

        return ret

    def get_dict(self):
        """Get Full Dict"""

        ret = self.db.hgetall(self.full_key)
        if not ret:
            raise RedisObjectError("Get Failed")

        return ret

    def set_dict(self, d):
        """Set Full Dict"""

        if self.schema is not None:
            s = set(d.keys())
            if not s.issubset(self.schema):
                raise KeyError("Keys {:s} do not match schema {:s}".format(s, self.schema))

        ret = self.db.hmset(self.full_key, d)
        if not ret:
            raise RedisObjectError("Set Failed")


class RedisSetBase(RedisObjectBase):
    """
    Redis Set Base Class

    """

    @classmethod
    def from_new(cls, v, key=None):
        """New Constructor"""

        # Check Input
        if not v:
            raise RedisObjectError("Input set must not be None or empty")

        # Call Parent
        obj = super(RedisSetBase, cls).from_new(key)

        # Add lst to DB
        if not obj.db.sadd(obj.full_key, *v):
            raise RedisObjectError("Create Failed")

        # Return Object
        return obj

    def get_set(self):
        """Get All Vals from Set"""

        return self.db.smembers(self.full_key)

    def add_vals(self, v):
        """Add Vals to Set"""

        return self.db.sadd(self.full_key, *v)

    def del_vals(self, v):
        """Remove Vals from Set"""

        return self.db.srem(self.full_key, *v)
