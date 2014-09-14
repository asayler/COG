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
import sys
import uuid
import zipfile
import shutil
import logging

import config

import backend_redis as backend
from backend_redis import BackendError, FactoryError, PersistentObjectError, ObjectDNE
import testrun

import repmod_moodle
import tester_script
import tester_io

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())


### Constants ###

_FILE_SCHEMA = ['key', 'name', 'type', 'encoding', 'path']
_REPORTER_SCHEMA = ['mod']
_REPORTER_DEFAULTS = {}
_ASSIGNMENT_SCHEMA = ['name', 'env', 'duedate', 'accepting_submissions', 'accepting_runs']
_ASSIGNMENT_DEFAULTS = {'duedate': "", 'accepting_submissions': "0", 'accepting_runs': "1"}
_TEST_SCHEMA = ['assignment', 'name', 'maxscore', 'tester']
_TEST_DEFAULTS = {}
_SUBMISSION_SCHEMA = ['assignment']
_RUN_SCHEMA = ['submission', 'test', 'assignment', 'status', 'score', 'retcode', 'output']


### COGS Core Objects ###

## Top-Level Server Object ##
class Server(object):
    """COGS Server Class"""

    # Override Constructor
    def __init__(self):
        """Base Constructor"""

        # Call Parent Construtor
        super(Server, self).__init__()

        # Call Setups
        File.setup()

        # Setup Factories
        self.FileFactory = FileUUIDFactory()
        self.ReporterFactory = backend.UUIDFactory(Reporter)
        self.AssignmentFactory = backend.UUIDFactory(Assignment)
        self.SubmissionFactory = backend.UUIDFactory(Submission)
        self.TestFactory = backend.UUIDFactory(Test)
        self.RunFactory = backend.UUIDFactory(Run)

    # Cleanup Up Server
    def close(self):
        pass

    # File Methods
    def create_file(self, data, file_obj=None, dst=None, owner=None):
        return self.FileFactory.from_new(data, file_obj=file_obj, dst=dst, owner=owner)
    def create_files(self, data, archive_obj=None, owner=None):
        return self.FileFactory.from_archive(data, archive_obj=archive_obj, owner=owner)
    def get_file(self, uuid_hex):
        return self.FileFactory.from_existing(uuid_hex)
    def list_files(self):
        return self.FileFactory.list_siblings()

    # Reporter Methods
    def create_reporter(self, data, owner=None):
        return self.ReporterFactory.from_new(data, owner=owner)
    def get_reporter(self, uuid_hex):
        return self.ReporterFactory.from_existing(uuid_hex)
    def list_reporters(self):
        return self.ReporterFactory.list_siblings()

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


## File Object ##
class File(backend.SchemaHash, backend.OwnedHash, backend.TSHash, backend.Hash):
    """COGS File Class"""

    @classmethod
    def setup(cls):

        # Create File Path Directory if not existing
        file_dir = os.path.abspath("{:s}".format(config.FILESTORAGE_PATH))
        if not os.path.isdir(file_dir):
            os.makedirs(file_dir)

    # Override from_new
    @classmethod
    def from_new(cls, data, **kwargs):
        """New Constructor"""

        # Extract Args
        file_obj = kwargs.pop('file_obj', None)
        if not file_obj:
            raise TypeError("file_obj required")

        # Set Schema
        schema = set(_FILE_SCHEMA)
        kwargs['schema'] = schema

        # Create New Object
        data = copy.copy(data)

        # Setup + Clean Name/Key/Path
        name = os.path.normpath(file_obj.filename)
        if not name:
            raise KeyError("Valid filename required")
        data['name'] = str(name)
        data['key'] = file_obj.name
        data['path'] = ""

        # Get Type
        typ = mimetypes.guess_type(file_obj.filename)
        data['type'] = str(typ[0])
        data['encoding'] = str(typ[1])

        # Call Parent
        fle = super(File, cls).from_new(data, **kwargs)

        # Set Path
        fle['path'] = os.path.abspath("{:s}/{:s}".format(config.FILESTORAGE_PATH, repr(fle)))

        # Save File
        try:
            file_obj.save(fle['path'])
        except IOError:
            # Clean up on failure
            fle.delete(force=True)
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


## File Factory Object ##
class FileUUIDFactory(backend.UUIDFactory):
    """File Factory"""

    def __init__(self, **kwargs):
        super(FileUUIDFactory, self).__init__(File, **kwargs)

    def from_archive(self, data, **kwargs):
        """Archive Constructor"""

        # Extract Args
        archive_obj = kwargs.pop('archive_obj', None)
        if not archive_obj:
            raise TypeError("archive_obj required")
        if kwargs.pop('file_obj', None):
            raise TypeError("from_archive does not take a file_obj")

        # Save archive
        archive_uuid = uuid.uuid4()
        archive_dir = os.path.abspath("{:s}/{:s}".format(config.ARCHIVE_PATH, archive_uuid))
        os.makedirs(archive_dir)
        archive_name = os.path.basename(archive_obj.filename)
        archive_name = werkzeug.utils.secure_filename(archive_name)
        archive_path = os.path.abspath("{:s}/{:s}".format(archive_dir, archive_name))
        archive_obj.save(archive_path)

        # Extract archive
        output_dir = os.path.abspath("{:s}/{:s}".format(archive_dir, 'extracted'))
        os.makedirs(output_dir)
        archive_type, archive_encoding = mimetypes.guess_type(archive_name)
        if archive_type == 'application/zip':
            if not zipfile.is_zipfile(archive_path):
                raise ValueError("Invalid zip file received: {:s}".format(archive_name))
            with zipfile.ZipFile(archive_path, 'r') as archive_zip:
                if archive_zip.testzip():
                    raise ValueError("Corrupted zip file received: {:s}".format(archive_name))
                archive_zip.extractall(output_dir)
        else:
            raise ValueError("Unsupported archive format: {:s}".format(archive_type))

        # Add extracted files to system
        fles = []
        try:
            for root, dirs, files in os.walk(output_dir):
                # TODO Ignore uneeded files: temp, git, etc
                for file_name in files:
                    src_path = os.path.abspath("{:s}/{:s}".format(root, file_name))
                    rel_path = os.path.relpath(src_path, output_dir)
                    src_file = open(src_path, 'rb')
                    key = "from_{:s}".format(archive_name)
                    file_obj = werkzeug.datastructures.FileStorage(stream=src_file,
                                                                   filename=rel_path,
                                                                   name=key)
                    # Create New Object
                    try:
                        fle = self.from_new(data, file_obj=file_obj, **kwargs)
                    except Exception as e:
                        raise
                    else:
                        fles.append(fle)
                    finally:
                        file_obj.close()
        except Exception as e:
            # Clean up on failure
            for fle in fles:
                fle.delete()
            raise
        else:
            # Return Files
            return fles
        finally:
            # Remove Archive Files
            shutil.rmtree(archive_dir)


## Reporter Object ##
class Reporter(backend.SchemaHash, backend.OwnedHash, backend.TSHash, backend.Hash):
    """COGS Reporter Class"""

    # Override from_new
    @classmethod
    def from_new(cls, data, **kwargs):

        # Process Args
        mod = data.get('mod', None)
        if not mod:
            raise KeyError("mod required")

        # Set Schema
        schema = set(_REPORTER_SCHEMA)
        if mod == 'moodle':
            schema.update(set(repmod_moodle.EXTRA_REPORTER_SCHEMA))
        else:
            raise Exception("Unknown repmod {:s}".format(mod))
        kwargs['schema'] = schema

        # Set Defaults
        defaults = copy.copy(_REPORTER_DEFAULTS)
        if mod == 'moodle':
            defaults.update(repmod_moodle.EXTRA_REPORTER_DEFAULTS)
        else:
            raise Exception("Unknown repmod {:s}".format(mod))
        for key in defaults:
            if key not in data:
                data[key] = defaults[key]

        # Call Parent
        reporter = super(Reporter, cls).from_new(data, **kwargs)

        # Return Reporter
        return reporter

    # Generate New Report
    def file_report(self, user, grade, comments):

        mod = self['mod']
        if mod == 'moodle':
            repmod = repmod_moodle
        else:
            raise Exception("Unknown repmod: {:s}".format(mod))

        repmod = repmod.Reporter(self)
        repmod.file_report(user, grade, comments)


## Reporter List Object ##
class ReporterList(backend.Set):
    """COGS Reporter List Class"""
    pass


## Assignment Object ##
class Assignment(backend.SchemaHash, backend.OwnedHash, backend.TSHash, backend.Hash):
    """COGS Assignment Class"""

    # Override Constructor
    def __init__(self, *args, **kwargs):
        """Assignment Constructor"""

        # Call Parent Construtor
        super(Assignment, self).__init__(*args, **kwargs)

        # Setup Factories
        self.SubmissionFactory = backend.UUIDFactory(Submission)
        self.TestFactory = backend.UUIDFactory(Test)

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

        # Set Defaults
        defaults = copy.copy(_ASSIGNMENT_DEFAULTS)
        for key in defaults:
            if key not in data:
                data[key] = defaults[key]

        # Call Parent
        assignment = super(Assignment, cls).from_new(data, **kwargs)

        # Return
        return assignment

    # Override Delete
    def delete(self):
        """Delete Assignment and Children"""

        # Remove Test Objects
        for tst_uuid in self.list_tests():
            tst = self.TestFactory.from_existing(tst_uuid)
            tst.delete()
        assert(not self.list_tests())

        # Remove Test List
        if self.tests.exists():
            self.tests.delete()

        # Remove Submission Objects
        for sub_uuid in self.list_submissions():
            sub = self.SubmissionFactory.from_existing(sub_uuid)
            sub.delete()
        assert(not self.list_submissions())

        # Remove Submission List
        if self.submissions.exists():
            self.submissions.delete()

        # Call Parent
        super(Assignment, self).delete()

    # Public Test Methods
    def create_test(self, data, owner=None):
        tst = self.TestFactory.from_new(data, asn=self, owner=owner)
        self._add_tests([str(tst.uuid)])
        return tst
    def list_tests(self):
        return self._list_tests()

    # Public Submission Methods
    def create_submission(self, data, owner=None):
        sub = self.SubmissionFactory.from_new(data, asn=self, owner=owner)
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

        # Setup Factories
        self.AssignmentFactory = backend.UUIDFactory(Assignment)
        self.FileFactory = FileUUIDFactory()
        self.ReporterFactory = backend.UUIDFactory(Reporter)

        # Setup Lists
        FileListFactory = backend.PrefixedFactory(FileList, prefix=self.full_key)
        self.files = FileListFactory.from_raw(key='files')
        ReporterListFactory = backend.PrefixedFactory(ReporterList, prefix=self.full_key)
        self.reporters = ReporterListFactory.from_raw(key='reporters')

    # Override from_new
    @classmethod
    def from_new(cls, data, **kwargs):

        # Extract Args
        asn = kwargs.pop('asn', None)
        if not asn:
            raise TypeError("Requires 'asn'")
        mod = data['tester']
        data = copy.copy(data)

        # Set Schema
        schema = set(_TEST_SCHEMA)
        if mod == 'script':
            schema.update(set(tester_script.EXTRA_TEST_SCHEMA))
        elif mod == 'io':
            schema.update(set(tester_io.EXTRA_TEST_SCHEMA))
        else:
            raise Exception("Unknown tester {:s}".format(mod))
        kwargs['schema'] = schema

        # Set Defaults
        defaults = copy.copy(_TEST_DEFAULTS)
        if mod == 'script':
            defaults.update(tester_script.EXTRA_TEST_DEFAULTS)
        elif mod == 'io':
            defaults.update(tester_io.EXTRA_TEST_DEFAULTS)
        else:
            raise Exception("Unknown tester {:s}".format(mod))
        for key in defaults:
            if key not in data:
                data[key] = defaults[key]

        # Set Assignment
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
            asn = self.AssignmentFactory.from_existing(asn_uuid)
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

        # Calculte Difference
        file_uuids = (set(file_uuids) - set(self.list_files()))

        # Check for Duplicate Names
        names = []
        for file_uuid in self.list_files():
            fle = self.FileFactory.from_existing(file_uuid)
            names.append(fle['name'])
        for file_uuid in file_uuids:
            fle = self.FileFactory.from_existing(file_uuid)
            if fle['name'] in names:
                raise PersistentObjectError("File named {:s} already in test".format(fle['name']))

        # Add to List
        return self.files.add_vals(file_uuids)

    def rem_files(self, file_uuids):
        return self.files.del_vals(file_uuids)

    def list_files(self):
        return self.files.get_set()

    # Reporters Methods
    def add_reporters(self, reporter_uuids):
        return self.reporters.add_vals(reporter_uuids)

    def rem_reporters(self, reporter_uuids):
        return self.reporters.del_vals(reporter_uuids)

    def list_reporters(self):
        return self.reporters.get_set()

    def get_reporters(self):
        rpts = []
        for rpt_uuid in self.list_reporters():
            rpts.append(self.ReporterFactory.from_existing(rpt_uuid))
        return rpts


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

        # Setup Factories
        self.AssignmentFactory = backend.UUIDFactory(Assignment)
        self.RunFactory = backend.UUIDFactory(Run)
        self.FileFactory = FileUUIDFactory()

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
            asn = self.AssignmentFactory.from_existing(asn_uuid)
            if not asn._rem_submissions([sub_uuid]):
                msg = "Could not remove Submission {:s} from Assignment {:s}".format(sub_uuid, asn_uuid)
                raise backend.PersistentObjectError(msg)

        # Remove run objects
        for run_uuid in self.list_runs():
            run = self.RunFactory.from_existing(run_uuid)
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

        # Calculte Difference
        file_uuids = (set(file_uuids) - set(self.list_files()))

        # Check for Duplicate Names
        names = []
        for file_uuid in self.list_files():
            fle = self.FileFactory.from_existing(file_uuid)
            names.append(fle['name'])
        for file_uuid in file_uuids:
            fle = self.FileFactory.from_existing(file_uuid)
            if fle['name'] in names:
                raise PersistentObjectError("File named {:s} already in test".format(fle['name']))

        # Add to List
        return self.files.add_vals(file_uuids)

    def rem_files(self, file_uuids):
        return self.files.del_vals(file_uuids)

    def list_files(self):
        return self.files.get_set()

    # Run Methods
    def execute_run(self, data, workers=None, owner=None):
        data = copy.copy(data)
        data['submission'] = str(self.uuid)
        data['assignment'] = self['assignment']
        run = self.RunFactory.from_new(data, workers=workers, owner=owner)
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

    # Override Constructor
    def __init__(self, *args, **kwargs):
        """Submission Constructor"""

        # Call Parent Construtor
        super(Run, self).__init__(*args, **kwargs)

        # Setup Factories
        self.AssignmentFactory = backend.UUIDFactory(Assignment)
        self.SubmissionFactory = backend.UUIDFactory(Submission)
        self.TestFactory = backend.UUIDFactory(Test)

    # Override from_new
    @classmethod
    def from_new(cls, data, **kwargs):
        """New Constructor"""

        # Process Args
        workers = kwargs.pop('workers')
        # if not workers:
        #     raise TypeError("Requires Workers")
        asn_uuid = data.get('assignment', None)
        if not asn_uuid:
            raise KeyError("Requires assignment")
        tst_uuid = data.get('test', None)
        if not tst_uuid:
            raise KeyError("Requires test")
        sub_uuid = data.get('submission', None)
        if not sub_uuid:
            raise KeyError("Requires submission")

        # Get Objects
        AssignmentFactory = backend.UUIDFactory(Assignment)
        SubmissionFactory = backend.UUIDFactory(Submission)
        TestFactory = backend.UUIDFactory(Test)
        tst = TestFactory.from_existing(tst_uuid)
        sub = SubmissionFactory.from_existing(sub_uuid)
        asn = AssignmentFactory.from_existing(asn_uuid)

        # Check Invariants
        assert(str(asn.uuid).lower() == tst['assignment'].lower())
        assert(str(asn.uuid).lower() == sub['assignment'].lower())

        # Set Schema
        schema = set(_RUN_SCHEMA)
        kwargs['schema'] = schema

        # Create New Object
        data = copy.copy(data)

        # Setup Dict
        data['status'] = "queued"
        data['score'] = ""
        data['retcode'] = ""
        data['output'] = ""

        # Create Run
        run = super(Run, cls).from_new(data, **kwargs)
        run_uuid = str(run.uuid).lower()

        # Add Task to Pool
        if workers:
            res = workers.apply_async(testrun.test, args=(asn, sub, tst, run))
        else:
            res = testrun.test(asn, sub, tst, run)

        # Return Run
        return run

    # Override Delete
    def delete(self, force=False):

        if not force:
            if not self.is_complete():
                logger.warning("Deleting run {:s} before complete...".format(self.uuid))

        # Remove from submission
        run_uuid = str(self.uuid)
        sub_uuid = self['submission']
        if sub_uuid:
            sub = self.SubmissionFactory.from_existing(sub_uuid)
            if not sub._rem_runs([run_uuid]):
                msg = "Could not remove Run {:s} from Submission {:s}".format(run_uuid, sub_uuid)
                logger.error(msg)
                raise backend.PersistentObjectError(msg)

        # Call Parent
        super(Run, self).delete()

    def is_complete(self):
        return self['status'].startswith('complete')


## Run List Object ##
class RunList(backend.Set):
    """COGS Run List Class"""
    pass
