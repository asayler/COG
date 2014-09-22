# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


import abc
import uuid
import collections
import time
import copy

_ENCODING = 'utf-8'
_FIELD_SEP = ':'
_TYPE_SEP = '+'

assert(_FIELD_SEP != _TYPE_SEP)


### Exceptions ###

class BackendError(Exception):
    """Base class for Backend Exceptions"""

    def __init__(self, *args, **kwargs):
        super(BackendError, self).__init__(*args, **kwargs)

class FactoryError(BackendError):
    """Backend Factory Exception"""

    def __init__(self, *args, **kwargs):
        super(FactoryError, self).__init__(*args, **kwargs)

class PersistentObjectError(BackendError):
    """Backend PersistentObject Exception"""

    def __init__(self, *args, **kwargs):
        super(PersistentObjectError, self).__init__(*args, **kwargs)

class ObjectDNE(PersistentObjectError):
    """Backend Object Does Not Exist"""

    def __init__(self, obj):
        msg = "{:s} does not exist.".format(obj)
        super(ObjectDNE, self).__init__(msg)


### Helpers ###

class abstractstaticmethod(staticmethod):
    __slots__ = ()
    def __init__(self, function):
        super(abstractstaticmethod, self).__init__(function)
        function.__isabstractmethod__ = True
    __isabstractmethod__ = True


class abstractclassmethod(classmethod):
    __slots__ = ()
    def __init__(self, function):
        super(abstractclassmethod, self).__init__(function)
        function.__isabstractmethod__ = True
    __isabstractmethod__ = True


### Abstract Factories ###

class PrefixedFactory(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, cls, prefix=None, typed=True, passthrough={}):

        # Call Parent
        super(PrefixedFactory, self).__init__()

        # Check Input
        if not issubclass(cls, PersistentObject):
            raise FactoryError("cls must be subclass of PersistentObject")

        # Save Vars
        self.cls = cls
        self.cls_name = cls.__name__.lower()
        self.prefix = prefix
        self.typed = typed
        self.passthrough = passthrough

    @abc.abstractmethod
    def list_family(self):
        """List Factory Objects"""
        pass

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

    def _generate_keys(self, key):

        # Sanitize Key
        if key:
            if _FIELD_SEP in str(key):
                raise PersistentObjectError("Key may not contain '{:s}'".format(_FIELD_SEP))
            if self.typed:
                if _TYPE_SEP in str(key):
                    raise PersistentObjectError("Key may not contain '{:s}'".format(_TYPE_SEP))

        # Set Keys
        if self.prefix:
            pre_key = str(self.prefix).lower()
        else:
            pre_key = ""

        if key:
            obj_key = str(key).lower()
            if self.typed:
                typ_key = "{:s}{:s}{:s}".format(self.cls_name, _TYPE_SEP, obj_key).lower()
        else:
            obj_key = ""
            if self.typed:
                typ_key = "{:s}".format(self.cls_name).lower()

        if pre_key:
            if self.typed:
                full_key = "{:s}{:s}{:s}".format(pre_key, _FIELD_SEP, typ_key).lower()
            else:
                full_key = "{:s}{:s}{:s}".format(pre_key, _FIELD_SEP, obj_key).lower()
        else:
            if self.typed:
                full_key = "{:s}".format(typ_key).lower()
            else:
                full_key = "{:s}".format(obj_key).lower()

        # Check Keys
        if not full_key:
            raise PersistentObjectError("full_key blank: object requires key, prefix, or typing")

        # Collect Keys
        keys = {'pre_key': pre_key,
                'obj_key': obj_key,
                'full_key': full_key,
                'key': full_key}
        if self.typed:
            keys['typ_key'] = typ_key

        # Return Keys
        return keys

    def _add_kwargs(self, func, *args, **kwargs):
        key = kwargs.pop('key', None)
        keys = self._generate_keys(key)
        kwargs.update(keys)
        kwargs.update(self.passthrough)
        return func(*args, **kwargs)

    def from_new(self, *args, **kwargs):
        return self._add_kwargs(self.cls.from_new, *args, **kwargs)

    def from_existing(self, *args, **kwargs):
        return self._add_kwargs(self.cls.from_existing, *args, **kwargs)

    def from_raw(self, *args, **kwargs):
        return self._add_kwargs(self.cls.from_raw, *args, **kwargs)


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


### Abstract Base Objects ###

class PersistentObject(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, **kwargs):
        """ Constructor"""

        # Get Key
        try:
            self.key = kwargs.pop('key')
        except KeyError:
            raise TypeError("'key' required")

        # Call Parent
        super(PersistentObject, self).__init__()

        # Set Vars
        for arg in kwargs:
            setattr(self, arg, kwargs[arg])

    def __unicode__(self):
        """Return Unicode Representation"""
        return unicode(repr(self))

    def __str__(self):
        """Return String Representation"""
        return unicode(self).encode(_ENCODING)

    def __repr__(self):
        """Return Unique Representation"""
        return "{:s}".format(self.key)

    def __hash__(self):
        """Return Hash"""
        return hash(repr(self))

    def __eq__(self, other):
        """Test Equality"""
        return (repr(self) == repr(other))

    @abstractclassmethod
    def from_new(cls, *args, **kwargs):
        """New Constructor"""
        return cls(*args, **kwargs)

    @abstractclassmethod
    def from_existing(cls, *args, **kwargs):
        """Existing Constructor"""
        return cls(*args, **kwargs)

    @classmethod
    def from_raw(cls, *args, **kwargs):
        """Raw Constructor"""
        return cls(*args, **kwargs)

    @abc.abstractmethod
    def delete(self):
        """Delete Object"""
        pass

    @abc.abstractmethod
    def exists(self):
        """Check if Object Exists"""
        pass


class TypedObject(PersistentObject):
    """
    Typed Object Class

    """

    def __init__(self, *args, **kwargs):
        """ Constructor"""

        # Get Type Key
        try:
            self.typ_key = kwargs.pop('typ_key')
        except KeyError:
            raise TypeError("'typ_key' required")

        # Call Parent
        super(TypedObject, self).__init__(*args, **kwargs)

    def __unicode__(self):
        """Return Unicode Representation"""
        return unicode(self.typ_key)

    def __str__(self):
        """Return String Representation"""
        return unicode(self).encode(_ENCODING)


### Abstract Set Objects ###

class Set(collections.MutableSet, TypedObject):
    """
    Set Object Class

    """

    @abc.abstractmethod
    def __len__(self):
        """Get Len of Set"""
        pass

    @abc.abstractmethod
    def __iter__(self):
        """Iterate Values"""
        pass

    @abc.abstractmethod
    def __contains__(self, val):
        """Check if Val in Set"""
        pass

    @abc.abstractmethod
    def add(self, val):
        """Add Val to Set"""
        pass

    @abc.abstractmethod
    def discard(self, val):
        """Remove Val from Set"""
        pass

    @abc.abstractmethod
    def get_set(self):
        """Get Static Set from Object"""
        pass

    @abc.abstractmethod
    def add_vals(self, vals):
        """Add Vals to Set"""
        pass

    @abc.abstractmethod
    def del_vals(self, vals):
        """Remove Vals from Set"""
        pass


### Abstract Hash Objects ###

class Hash(collections.MutableMapping, TypedObject):
    """
    Hash Object Class

    """

    @abc.abstractmethod
    def __len__(self):
        """Get Len of Hash"""
        pass

    @abc.abstractmethod
    def __iter__(self):
        """Iterate Keys"""
        pass

    @abc.abstractmethod
    def __getitem__(self, key):
        """Get Dict Item"""
        pass

    @abc.abstractmethod
    def __setitem__(self, key, val):
        """Set Dict Item"""
        pass

    @abc.abstractmethod
    def __delitem__(self, key):
        """Delete Dict Item"""
        pass

    @abc.abstractmethod
    def keys(self):
        """Get Dict Keys"""
        pass

    @abc.abstractmethod
    def get_dict(self):
        """Get Static Dict"""
        pass

    @abc.abstractmethod
    def set_dict(self, data):
        """Set from Static Dict"""
        pass


class TSHash(Hash):
    """
    Time-Stamped Hash Object Class

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

    def __setitem__(self, key, val):
        """Set Item"""

        # Set Time
        data = {}
        data['modified_time'] = str(time.time())

        # Set Value
        data[key] = val

        # Call Parent
        ret = super(TSHash, self).set_dict(data)

        # Return
        return ret

    def set_dict(self, data):
        """Set Dict"""

        # Set Time
        data = copy.copy(data)
        data['modified_time'] = str(time.time())

        # Call Parent
        ret = super(TSHash, self).set_dict(data)

        # Return
        return ret


class OwnedHash(Hash):
    """
    Owned Hash Object Class

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


class Schema(Set):
    """
    Schema Object Class

    """
    pass


class SchemaHash(Hash):
    """
    Schema-Enforced Hash Object Class

    """

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
