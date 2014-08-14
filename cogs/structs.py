# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


### Imports ###

import copy
import os
import time
import werkzeug
import mimetypes
import multiprocessing

import backend_redis as backend
from backend_redis import BackendError, FactoryError, PersistentObjectError, ObjectDNE
import testrun


### Constants ###

_NUM_WORKERS = 10

_ASSIGNMENT_SCHEMA = ['name', 'env']
_TEST_SCHEMA = ['assignment', 'name', 'maxscore', 'tester']
_SUBMISSION_SCHEMA = ['assignment']
_RUN_SCHEMA = ['submission', 'test', 'status', 'score', 'retcode', 'output']
_FILE_SCHEMA = ['key', 'name', 'type', 'encoding', 'path']

_DEFAULT_FILES_DIR = "./files/"
_FILES_DIR = os.environ.get('COGS_UPLOADED_FILES_PATH', _DEFAULT_FILES_DIR)


### COGS Core Objects ###

## Top-Level Server Object ##
class Server(object):
    """COGS Server Class"""

    # Override Constructor
    def __init__(self):
        """Base Constructor"""

        # Call Parent Construtor
        super(Server, self).__init__()

        # Setup Factories
        passthrough = {'srv': self}
        self.FileFactory = backend.UUIDFactory(File, passthrough=passthrough)
        self.AssignmentFactory = backend.UUIDFactory(Assignment, passthrough=passthrough)
        self.SubmissionFactory = backend.UUIDFactory(Submission, passthrough=passthrough)
        self.TestFactory = backend.UUIDFactory(Test, passthrough=passthrough)
        self.RunFactory = backend.UUIDFactory(Run, passthrough=passthrough)

        # Setup Worker Pool
        self.workers = multiprocessing.Pool(_NUM_WORKERS)

    # Cleanup Up Server
    def close(self):
        self.workers.close()
        self.workers.join()

    # File Methods
    def create_file(self, data, file_obj=None, dst=None, owner=None):
        return self.FileFactory.from_new(data, file_obj=file_obj, dst=dst, owner=owner)
    def get_file(self, uuid_hex):
        return self.FileFactory.from_existing(uuid_hex)
    def list_files(self):
        return self.FileFactory.list_siblings()

    # Assignment Methods
    def create_assignment(self, data, owner=None):
        return self.AssignmentFactory.from_new(data, owner=owner)
    def get_assignment(self, uuid_hex):
        return self.AssignmentFactory.from_existing(uuid_hex)
    def list_assignments(self):
        return self.AssignmentFactory.list_siblings()

    # Test Methods
    def get_test(self, uuid_hex):
        return self.TestFactory.from_existing(uuid_hex)
    def list_tests(self):
        return self.TestFactory.list_siblings()

    # Submission Methods
    def get_submission(self, uuid_hex):
        return self.SubmissionFactory.from_existing(uuid_hex)
    def list_submissions(self):
        return self.SubmissionFactory.list_siblings()

    # Run Methods
    def get_run(self, uuid_hex):
        return self.RunFactory.from_existing(uuid_hex)
    def list_runs(self):
        return self.RunFactory.list_siblings()


## Assignment Object ##
class Assignment(backend.SchemaHash, backend.OwnedHash, backend.TSHash, backend.Hash):
    """COGS Assignment Class"""

    # Override Constructor
    def __init__(self, *args, **kwargs):
        """Assignment Constructor"""

        # Call Parent Construtor
        super(Assignment, self).__init__(*args, **kwargs)

        # Setup Lists
        TestListFactory = backend.PrefixedFactory(TestList, prefix=self.full_key)
        self.tests = TestListFactory.from_raw(key='tests')
        SubmissionListFactory = backend.PrefixedFactory(SubmissionList, prefix=self.full_key)
        self.submissions = SubmissionListFactory.from_raw(key='submissions')

    # Override from_new
    @classmethod
    def from_new(cls, data, **kwargs):

        # Set Schema
        schema = set(_ASSIGNMENT_SCHEMA)
        kwargs['schema'] = schema

        # Call Parent
        assignment = super(Assignment, cls).from_new(data, **kwargs)

        # Return
        return assignment

    # Override Delete
    def delete(self):
        """Delete Assignment and Children"""

        # Remove Test Objects
        for tst_uuid in self.list_tests():
            tst = self.srv.get_test(tst_uuid)
            tst.delete()
        assert(not self.list_tests())

        # Remove Test List
        if self.tests.exists():
            self.tests.delete()

        # Remove Submission Objects
        for sub_uuid in self.list_submissions():
            sub = self.srv.get_submission(sub_uuid)
            sub._delete()
        assert(not self.list_submissions())

        # Remove Submission List
        if self.submissions.exists():
            self.submissions.delete()

        # Call Parent
        super(Assignment, self).delete()

    # Public Test Methods
    def create_test(self, dictionary, owner=None):
        tst = self.srv.TestFactory.from_new(dictionary, asn=self, owner=owner)
        self._add_tests([str(tst.uuid)])
        return tst
    def list_tests(self):
        return self._list_tests()

    # Public Submission Methods
    def create_submission(self, dictionary, owner=None):
        sub = self.srv.SubmissionFactory.from_new(dictionary, asn=self, owner=owner)
        self._add_submissions([str(sub.uuid)])
        return sub
    def list_submissions(self):
        return self._list_submissions()

    # Private Test Methods
    def _add_tests(self, test_uuids):
        return self.tests.add_vals(test_uuids)
    def _rem_tests(self, test_uuids):
        return self.tests.del_vals(test_uuids)
    def _list_tests(self):
        return self.tests.get_set()

    # Private Submission Methods
    def _add_submissions(self, submission_uuids):
        return self.submissions.add_vals(submission_uuids)
    def _rem_submissions(self, submission_uuids):
        return self.submissions.del_vals(submission_uuids)
    def _list_submissions(self):
        return self.submissions.get_set()


## Test Object ##
class Test(backend.SchemaHash, backend.OwnedHash, backend.TSHash, backend.Hash):
    """COGS Test Class"""

    # Override Constructor
    def __init__(self, *args, **kwargs):
        """Test Constructor"""

        # Call Parent Construtor
        super(Test, self).__init__(**kwargs)

        # Setup Lists
        FileListFactory = backend.PrefixedFactory(FileList, prefix=self.full_key)
        self.files = FileListFactory.from_raw(key='files')

    # Override from_new
    @classmethod
    def from_new(cls, data, **kwargs):

        # Extract Args
        try:
            asn = kwargs.pop('asn')
        except KeyError:
            raise TypeError("Requires 'asn'")

        # Set Schema
        schema = set(_TEST_SCHEMA)
        kwargs['schema'] = schema

        # Set Assignment
        data = copy.copy(data)
        if asn:
            data['assignment'] = str(asn.uuid).lower()
        else:
            data['assignment'] = ""

        # Call Parent
        obj = super(Test, cls).from_new(data, **kwargs)

        # Return Test
        return obj

    # Override Delete
    def delete(self):
        """Delete Test"""

        # Remove from assignment
        tst_uuid = str(self.uuid)
        asn_uuid = self['assignment']
        if asn_uuid:
            asn = self.srv.get_assignment(asn_uuid)
            if not asn._rem_tests([tst_uuid]):
                msg = "Could not remove Test {:s} from Assignment {:s}".format(tst_uuid, asn_uuid)
                raise backend.PersistentObjectError(msg)

        # Remove file list
        if self.files.exists():
            self.files.delete()

        # Call Parent
        super(Test, self).delete()

    # Files Methods
    def add_files(self, file_uuids):
        return self.files.add_vals(file_uuids)
    def rem_files(self, file_uuids):
        return self.files.del_vals(file_uuids)
    def list_files(self):
        return self.files.get_set()


## Test List Object ##
class TestList(backend.Set):
    """COGS Test List Class"""
    pass


## Submission Object ##
class Submission(backend.SchemaHash, backend.OwnedHash, backend.TSHash, backend.Hash):
    """COGS Submission Class"""

    # Override Constructor
    def __init__(self, *args, **kwargs):
        """Submission Constructor"""

        # Call Parent Construtor
        super(Submission, self).__init__(*args, **kwargs)

        # Setup Lists
        FileListFactory = backend.PrefixedFactory(FileList, prefix=self.full_key)
        self.files = FileListFactory.from_raw(key='files')
        RunListFactory = backend.PrefixedFactory(RunList, prefix=self.full_key)
        self.runs = RunListFactory.from_raw(key='runs')

    # Override from_new
    @classmethod
    def from_new(cls, data, **kwargs):

        # Extract Args
        try:
            asn = kwargs.pop('asn')
        except KeyError:
            raise TypeError("Requires 'asn'")

        # Set Schema
        schema = set(_SUBMISSION_SCHEMA)
        kwargs['schema'] = schema

        # Set Assignment
        data = copy.copy(data)
        if asn:
            data['assignment'] = str(asn.uuid).lower()
        else:
            data['assignment'] = ""

        # Call Parent
        obj = super(Submission, cls).from_new(data, **kwargs)

        # Return Submission
        return obj

    # Override Delete
    def delete(self):
        """Delete Submission and Children"""

        # Remove from assignment
        sub_uuid = str(self.uuid)
        asn_uuid = self['assignment']
        if asn_uuid:
            asn = self.srv.get_assignment(asn_uuid)
            if not asn._rem_submissions([sub_uuid]):
                msg = "Could not remove Submission {:s} from Assignment {:s}".format(sub_uuid, asn_uuid)
                raise backend.PersistentObjectError(msg)

        # Remove run objects
        for run_uuid in self.list_runs():
            run = self.srv.get_run(run_uuid)
            run.delete()
        assert(not self.list_runs())

        # Remove run list
        if self.runs.exists():
            self.runs.delete()

        # Remove file list
        if self.files.exists():
            self.files.delete()

        # Call Parent
        super(Submission, self).delete()

    # Files Methods
    def add_files(self, file_uuids):
        return self.files.add_vals(file_uuids)
    def rem_files(self, file_uuids):
        return self.files.del_vals(file_uuids)
    def list_files(self):
        return self.files.get_set()

    # Run Methods
    def execute_run(self, tst, owner=None):
        run = self.srv.RunFactory.from_new(tst, self, owner=owner)
        self._add_runs([str(run.uuid)])
        return run
    def list_runs(self):
        return self._list_runs()

    # Private Runs Methods
    def _add_runs(self, run_uuids):
        return self.runs.add_vals(run_uuids)
    def _rem_runs(self, run_uuids):
        return self.runs.del_vals(run_uuids)
    def _list_runs(self):
        return self.runs.get_set()


## Submission List Object ##
class SubmissionList(backend.Set):
    """COGS Submission List Class"""
    pass


## Test Run Object ##
class Run(backend.SchemaHash, backend.OwnedHash, backend.TSHash, backend.Hash):
    """COGS Run Class"""

    # Override from_new
    @classmethod
    def from_new(cls, tst, sub, **kwargs):
        """New Constructor"""

        # Get Assignment
        assert(sub['assignment'] == tst['assignment'])
        asn = cls.srv.get_assignment(sub['assignment'])

        # Set Schema
        schema = set(_RUN_SCHEMA)
        kwargs['schema'] = schema

        # Create New Object
        data = {}

        # Setup Dict
        data['submission'] = str(sub.uuid)
        data['test'] = str(tst.uuid)
        data['status'] = "queued"
        data['score'] = ""
        data['retcode'] = ""
        data['output'] = ""

        # Create Run
        run = super(Run, cls).from_new(data, **kwargs)

        # Add Task to Pool
        res = cls.srv.workers.apply_async(testrun.test, args=(asn, sub, tst, run))
        print(res.get())

        # Return Run
        return run

    # Override Delete
    def delete(self, force=False):

        # TODO Prevent delete while still running
        if not force:
            while not self['status'].startswith('complete'):
                print("Waiting for run to complete...")
                time.sleep(1)

        # Remove from submission
        run_uuid = str(self.uuid)
        sub_uuid = self['submission']
        if sub_uuid:
            sub = self.srv.get_submission(sub_uuid)
            if not sub._rem_runs([run_uuid]):
                msg = "Could not remove Run {:s} from Submission {:s}".format(run_uuid, sub_uuid)
                raise backend.PersistentObjectError(msg)

        # Call Parent
        super(Run, self).delete()


## Run List Object ##
class RunList(backend.Set):
    """COGS Run List Class"""
    pass


## File Object ##
class File(backend.SchemaHash, backend.OwnedHash, backend.TSHash, backend.Hash):
    """COGS File Class"""

    # Override from_new
    @classmethod
    def from_new(cls, data, **kwargs):
        """New Constructor"""

        # Extract Args
        file_obj = kwargs.pop('file_obj', None)
        dst = kwargs.pop('dst', None)

        # Set Schema
        schema = set(_FILE_SCHEMA)
        kwargs['schema'] = schema

        # Create New Object
        data = copy.copy(data)

        # Setup file_obj
        if file_obj is None:
            src_path = os.path.abspath("{:s}".format(data['path']))
            src_file = open(src_path, 'rb')
            file_obj = werkzeug.datastructures.FileStorage(stream=src_file, filename=data['name'])

        # Setup data
        data['name'] = str(file_obj.filename)
        data['path'] = ""

        # Get Type
        typ = mimetypes.guess_type(file_obj.filename)
        data['type'] = str(typ[0])
        data['encoding'] = str(typ[1])

        # Call Parent
        fle = super(File, cls).from_new(data, **kwargs)

        # Set Path
        if dst is None:
            fle['path'] = os.path.abspath("{:s}/{:s}".format(_FILES_DIR, repr(fle)))
        else:
            fle['path'] = os.path.abspath("{:s}".format(dst))

        # Save File
        try:
            file_obj.save(fle['path'])
        except IOError:
            # Clean up on failure
            fle._delete(force=True)
            raise

        # Return File
        return fle

    # Override Delete
    def delete(self, force=False):
        """Delete Object"""

        # Delete File
        try:
            os.remove(self['path'])
        except OSError:
            if force:
                pass
            else:
                raise

        # Delete Self
        super(File, self).delete()


## File List Object ##
class FileList(backend.Set):
    """COGS File List Class"""
    pass
