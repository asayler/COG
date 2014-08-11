#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import copy

import backend


class SubMixin(object):

    def subHashDirectHelper(self, hash_create, hash_get, hash_list, input_dict,
                            base_kwargs={}, extra_kwargs={}, extra_objs=None):

        if extra_objs:
            uuids_in = set(extra_objs)
        else:
            uuids_in = set([])

        # List UUIDs (Empty DB)
        uuids_out = hash_list()
        self.assertEqual(uuids_in, uuids_out)

        # Generate 10 Objects
        objects = []
        for i in range(10):
            kwargs = copy.copy(extra_kwargs)
            for kwarg in base_kwargs:
                kwargs[kwarg] = "{:s}_{:02d}".format(base_kwargs[kwarg], i)
            obj = hash_create(input_dict, **kwargs)
            self.assertSubset(input_dict, obj.get_dict())
            objects.append(obj)
            uuids_in.add(str(obj.uuid))

        # List UUIDs
        uuids_out = hash_list()
        self.assertEqual(uuids_in, uuids_out)

        # Check Objects
        for obj_in in objects:
            obj_out = hash_get(str(obj_in.uuid))
            self.assertEqual(obj_in, obj_out)
            self.assertSubset(obj_in.get_dict(), obj_out.get_dict())

        # Delete Objects
        for obj_in in objects:
            uuid = str(obj_in.uuid)
            obj_in.delete()
            self.assertFalse(obj_in.exists())
            uuids_in.remove(uuid)

        # List UUIDs (Empty DB)
        uuids_out = hash_list()
        self.assertEqual(uuids_in, uuids_out)

    def subSetReferenceHelper(self, set_add, set_rem, set_list, uuids,
                              extra_uuids=None):

        uuids_in = set(uuids)

        if extra_uuids:
            objects_in = set(extra_uuids)
        else:
            objects_in = set([])

        # List Objects (Empty DB)
        objects_out = set_list()
        self.assertEqual(objects_in, objects_out)

        # Add Set
        self.assertEqual(set_add(set(uuids_in)), len(uuids_in))
        objects_in.update(set(uuids_in))

        # List Objects
        objects_out = set_list()
        self.assertEqual(objects_in, objects_out)

        # Remove Some Objects
        for i in range(len(uuids_in)/2):
            k = uuids_in.pop()
            self.assertEqual(set_rem(set([k])), 1)
            objects_in.remove(k)

        # List Objects
        objects_out = set_list()
        self.assertEqual(objects_in, objects_out)

        # Remove Remaining Objects
        self.assertEqual(set_rem(uuids_in), len(uuids_in))
        objects_in.difference_update(set(uuids_in))

        # List Objects (Empty List)
        objects_out = set_list()
        self.assertEqual(objects_in, objects_out)


class UUIDHashMixin(object):

    def hashCreateHelper(self, hash_create, input_dict, extra_kwargs={}):

        if input_dict:
            # Test Empty Dict
            d = {}
            self.assertRaises(KeyError, hash_create, d, **extra_kwargs)

        if input_dict:
            # Test Sub Dict
            d = copy.copy(input_dict)
            d.pop(d.keys()[0])
            self.assertRaises(KeyError, hash_create, d, **extra_kwargs)

        # Test Bad Dict
        d = {'badkey': "test"}
        self.assertRaises(KeyError, hash_create, d, **extra_kwargs)

        # Test Super Dict
        d = copy.copy(input_dict)
        d['badkey'] = "test"
        self.assertRaises(KeyError, hash_create, d, **extra_kwargs)

        # Test Good Dict
        obj = hash_create(input_dict, **extra_kwargs)
        self.assertSubset(input_dict, obj.get_dict())

        # Delete Obj
        obj.delete()
        self.assertFalse(obj.exists())

    def hashGetHelper(self, hash_create, hash_get, input_dict, extra_kwargs={}):

        # Test Invalid UUID
        self.assertRaises(backend.ObjectDNE,
                          hash_get,
                          'eb424026-6f54-4ef8-a4d0-bb658a1fc6cf')

        # Test Valid UUID
        obj1 = hash_create(input_dict, **extra_kwargs)
        self.assertSubset(input_dict, obj1.get_dict())
        obj1_key = obj1.obj_key
        obj2 = hash_get(obj1_key)
        self.assertEqual(obj1, obj2)
        self.assertEqual(obj1.get_dict(), obj2.get_dict())

        # Delete Obj
        obj1.delete()
        self.assertFalse(obj1.exists())

    def hashUpdateHelper(self, hash_create, input_dict, extra_kwargs={}):

        # Create Obj
        obj = hash_create(input_dict, **extra_kwargs)
        self.assertSubset(input_dict, obj.get_dict())

        # Update Obj
        update_dict = {}
        for k in input_dict:
            update_dict[k] = "{:s}_updated".format(input_dict[k])
        obj.update(update_dict)
        self.assertSubset(update_dict, obj.get_dict())

        # Delete Obj
        obj.delete()
        self.assertFalse(obj.exists())

    def hashDeleteHelper(self, hash_create, input_dict, extra_kwargs={}):

        # Test Valid UUID
        obj = hash_create(input_dict, **extra_kwargs)
        obj.delete()
        self.assertFalse(obj.exists())


class SetMixin(object):

    pass
