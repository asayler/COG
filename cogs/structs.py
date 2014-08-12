# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import copy
import os
import time
import werkzeug
import mimetypes
import multiprocessing

import backend_redis as backend
from backend_redis import BackendError, FactoryError, ObjectError, ObjectDNE
import testrun


_NUM_WORKERS = 10

_ASSIGNMENT_SCHEMA = ['owner', 'name', 'env']
_TEST_SCHEMA = ['owner', 'assignment', 'name', 'maxscore', 'tester']
_SUBMISSION_SCHEMA = ['owner', 'assignment']
_RUN_SCHEMA = ['owner', 'submission', 'test', 'status', 'score', 'retcode', 'output']
_FILE_SCHEMA = ['owner', 'key', 'name', 'type', 'encoding', 'path']

_FILES_DIR = "./files/"


### COGS Core Objects ###

## Top-Level Server Object ##
class Server(object):
    """COGS Server Class"""

    # Override Constructor
    def __init__(self, db=None):
        """Base Constructor"""

        # Call Parent Construtor
        super(Server, self).__init__()

        # Save vars
        self.db = db

        # Setup Factories
        self.FileFactory = backend.UUIDFactory(FileBase, db=self.db, srv=self)
        self.AssignmentFactory = backend.UUIDFactory(AssignmentBase, db=self.db, srv=self)
        self.SubmissionFactory = backend.UUIDFactory(SubmissionBase, db=self.db, srv=self)
        self.TestFactory = backend.UUIDFactory(TestBase, db=self.db, srv=self)
        self.RunFactory = backend.UUIDFactory(RunBase, db=self.db, srv=self)

        # Setup Worker Pool
        self.workers = multiprocessing.Pool(_NUM_WORKERS)

    # Cleanup Up Server
    def close(self):
        self.workers.close()
        self.workers.join()

    # File Methods
    def create_file(self, data, file_obj=None, dst=None, user=None):
        return self.FileFactory.from_new(data, file_obj=file_obj, dst=dst, user=user)
    def get_file(self, uuid_hex):
        return self.FileFactory.from_existing(uuid_hex)
    def list_files(self):
        return self.FileFactory.list_siblings()

    # Assignment Methods
    def create_assignment(self, data, user=None):
        return self.AssignmentFactory.from_new(data, user=user)
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


### COGS Base Objects ###

## Assignment Object ##
class AssignmentBase(backend.OwnedTSHashBase):
    """COGS Assignment Class"""

    schema = set(backend.TS_SCHEMA + _ASSIGNMENT_SCHEMA)

    # Override Constructor
    def __init__(self, key=None):
        """Base Constructor"""

        # Call Parent Construtor
        super(AssignmentBase, self).__init__(key)

        # Setup Lists
        TestListFactory = backend.Factory(TestListBase, prefix=self.full_key,
                                          db=self.db, srv=self.srv)
        self.tests = TestListFactory.from_raw('tests')
        SubmissionListFactory = backend.Factory(SubmissionListBase, prefix=self.full_key,
                                                db=self.db, srv=self.srv)
        self.submissions = SubmissionListFactory.from_raw('submissions')

    # Override Delete
    def delete(self):

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
        super(AssignmentBase, self).delete()

    # Public Test Methods
    def create_test(self, dictionary, user=None):
        tst = self.srv.TestFactory.from_new(dictionary, asn=self, user=user)
        self._add_tests([str(tst.uuid)])
        return tst
    def list_tests(self):
        return self._list_tests()

    # Public Submission Methods
    def create_submission(self, dictionary, user=None):
        sub = self.srv.SubmissionFactory.from_new(dictionary, asn=self, user=user)
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
class TestBase(backend.OwnedTSHashBase):
    """COGS Test Class"""

    schema = set(backend.TS_SCHEMA + _TEST_SCHEMA)

    # Override Constructor
    def __init__(self, uuid_obj):
        """Base Constructor"""

        # Call Parent Construtor
        super(TestBase, self).__init__(uuid_obj)

        # Setup Lists
        FileListFactory = backend.Factory(FileListBase, prefix=self.full_key, db=self.db, srv=self.srv)
        self.files = FileListFactory.from_raw('files')

    # Override Delete
    def delete(self):

        # Remove from assignment
        tst_uuid = str(self.uuid)
        asn_uuid = self['assignment']
        if asn_uuid:
            asn = self.srv.get_assignment(asn_uuid)
            if not asn._rem_tests([tst_uuid]):
                msg = "Could not remove Test {:s} from Assignment {:s}".format(tst_uuid, asn_uuid)
                raise backend.ObjectError(msg)

        # Remove file list
        if self.files.exists():
            self.files.delete()

        # Call Parent
        super(TestBase, self).delete()

    # Override from_new
    @classmethod
    def from_new(cls, data, asn=None, **kwargs):

        # Set Assignment
        data = copy.copy(data)
        if asn:
            data['assignment'] = str(asn.uuid).lower()
        else:
            data['assignment'] = ""

        # Call Parent
        obj = super(TestBase, cls).from_new(data, **kwargs)

        # Return Test
        return obj

    # Files Methods
    def add_files(self, file_uuids):
        return self.files.add_vals(file_uuids)
    def rem_files(self, file_uuids):
        return self.files.del_vals(file_uuids)
    def list_files(self):
        return self.files.get_set()


## Test List Object ##
class TestListBase(backend.SetBase):
    """COGS Test List Class"""
    pass


## Submission Object ##
class SubmissionBase(backend.OwnedTSHashBase):
    """COGS Submission Class"""

    schema = set(backend.TS_SCHEMA + _SUBMISSION_SCHEMA)

    # Override Constructor
    def __init__(self, uuid_obj):
        """Base Constructor"""

        # Call Parent Construtor
        super(SubmissionBase, self).__init__(uuid_obj)

        # Setup Lists
        FileListFactory = backend.Factory(FileListBase, prefix=self.full_key, db=self.db, srv=self.srv)
        self.files = FileListFactory.from_raw('files')
        RunListFactory = backend.Factory(RunListBase, prefix=self.full_key, db=self.db, srv=self.srv)
        self.runs = RunListFactory.from_raw('runs')

    # Override Delete
    def delete(self):

        # Remove from assignment
        sub_uuid = str(self.uuid)
        asn_uuid = self['assignment']
        if asn_uuid:
            asn = self.srv.get_assignment(asn_uuid)
            if not asn._rem_submissions([sub_uuid]):
                msg = "Could not remove Submission {:s} from Assignment {:s}".format(sub_uuid, asn_uuid)
                raise backend.ObjectError(msg)

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
        super(SubmissionBase, self).delete()

    # Override from_new
    @classmethod
    def from_new(cls, data, asn=None, **kwargs):

        # Set Assignment
        data = copy.copy(data)
        if asn:
            data['assignment'] = str(asn.uuid).lower()
        else:
            data['assignment'] = ""

        # Call Parent
        obj = super(SubmissionBase, cls).from_new(data, **kwargs)

        # Return Submission
        return obj

    # Files Methods
    def add_files(self, file_uuids):
        return self.files.add_vals(file_uuids)
    def rem_files(self, file_uuids):
        return self.files.del_vals(file_uuids)
    def list_files(self):
        return self.files.get_set()

    # Run Methods
    def execute_run(self, tst, user=None):
        run = self.srv.RunFactory.from_new(tst, self, user=user)
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
class SubmissionListBase(backend.SetBase):
    """COGS Submission List Class"""
    pass


## Test Run Object ##
class RunBase(backend.OwnedTSHashBase):
    """COGS Run Class"""

    schema = set(backend.TS_SCHEMA + _RUN_SCHEMA)

    # Override from_new
    @classmethod
    def from_new(cls, tst, sub, **kwargs):
        """New Constructor"""

        # Get Assignment
        assert(sub['assignment'] == tst['assignment'])
        asn = cls.srv.get_assignment(sub['assignment'])

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
        run = super(RunBase, cls).from_new(data, **kwargs)

        # Add Task to Pool
        res = cls.srv.workers.apply_async(testrun.test, args=(asn, sub, tst, run))
        print(res.get())

        # Return Run
        return run

    # Override Delete
    def delete(self, force=False):

        # TODO Prevent delete while still running
        if not force:
            while self['status'].startswith('complete'):
                print("Waiting for run to complete...")
                time.sleep(1)

        # Remove from submission
        run_uuid = str(self.uuid)
        sub_uuid = self['submission']
        if sub_uuid:
            sub = self.srv.get_submission(sub_uuid)
            if not sub._rem_runs([run_uuid]):
                msg = "Could not remove Run {:s} from Submission {:s}".format(run_uuid, sub_uuid)
                raise backend.ObjectError(msg)

        # Call Parent
        super(RunBase, self).delete()


## Run List Object ##
class RunListBase(backend.SetBase):
    """COGS Run List Class"""
    pass


## File Object ##
class FileBase(backend.OwnedTSHashBase):
    """COGS File Class"""

    schema = set(backend.TS_SCHEMA + _FILE_SCHEMA)

    # Override from_new
    @classmethod
    def from_new(cls, data, file_obj=None, dst=None, **kwargs):
        """New Constructor"""

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

        # Create File
        fle = super(FileBase, cls).from_new(data, **kwargs)

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
        super(FileBase, self).delete()


## File List Object ##
class FileListBase(backend.SetBase):
    """COGS File List Class"""
    pass
