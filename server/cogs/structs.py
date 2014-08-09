# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import copy
import os
import werkzeug
import mimetypes

import auth

import backend_redis as backend
from backend_redis import BackendError, FactoryError, ObjectError, ObjectDNE


_TS_SCHEMA = ['created_time', 'modified_time']
_USER_SCHEMA = ['username', 'first', 'last', 'auth']
_GROUP_SCHEMA = ['name']
_ASSIGNMENT_SCHEMA = ['owner', 'name']
_TEST_SCHEMA = ['owner', 'assignment', 'name', 'type', 'maxscore']
_SUBMISSION_SCHEMA = ['owner', 'assignment']
_RUN_SCHEMA = ['owner', 'submission', 'test', 'status', 'score', 'output']
_FILE_SCHEMA = ['owner', 'key', 'name', 'type', 'encoding', 'path']

_FILES_DIR = "./files/"


### COGS Core Objects ###

## Top-Level Server Object ##
class Server(auth.AuthorizationAdminMixin, auth.AuthorizationMgmtMixin, object):
    """COGS Server Class"""

    # Override Constructor
    def __init__(self, db=None):
        """Base Constructor"""

        # Call Parent Construtor
        super(Server, self).__init__()

        # Save vars
        self.db = db
        self.srv = self

        # Setup Factories
        self.UserFactory = backend.UUIDFactory(UserBase, db=self.db, srv=self.srv)
        self.GroupFactory = backend.UUIDFactory(GroupBase, db=self.db, srv=self.srv)
        self.FileFactory = backend.UUIDFactory(FileBase, db=self.db, srv=self.srv)
        self.AssignmentFactory = backend.UUIDFactory(AssignmentBase, db=self.db, srv=self.srv)
        self.SubmissionFactory = backend.UUIDFactory(SubmissionBase, db=self.db, srv=self.srv)
        self.TestFactory = backend.UUIDFactory(TestBase, db=self.db, srv=self.srv)

        # Setup Admins
        self.init_admins()

    # User Methods
    @auth.requires_authorization()
    def list_users(self):
        return self._list_users()
    @auth.requires_authorization()
    def create_user(self, data):
        return self._create_user(data)
    @auth.requires_authorization()
    def get_user(self, user_uuid):
        return self._get_user(user_uuid)

    # Group Methods
    @auth.requires_authorization()
    def list_groups(self):
        return self._list_groups()
    @auth.requires_authorization()
    def create_group(self, data):
        return self._create_group(data)
    @auth.requires_authorization()
    def get_group(self, group_uuid):
        return self._get_group(group_uuid)

    # File Methods
    @auth.requires_authorization(pass_user=True)
    def create_file(self, data, file_obj=None, dst=None, user=None):
        return self._create_file(data, file_obj=file_obj, dst=dst, user=user)
    @auth.requires_authorization()
    def get_file(self, uuid_hex):
        return self._get_file(uuid_hex)
    @auth.requires_authorization()
    def list_files(self):
        return self._list_files()

    # Assignment Methods
    @auth.requires_authorization(pass_user=True)
    def create_assignment(self, data, user=None):
        return self._create_assignment(data, user=user)
    @auth.requires_authorization()
    def get_assignment(self, uuid_hex):
        return self._get_assignment(uuid_hex)
    @auth.requires_authorization()
    def list_assignments(self):
        return self._list_assignments()

    # Test Methods
    @auth.requires_authorization()
    def get_test(self, uuid_hex):
        return self._get_test(uuid_hex)
    @auth.requires_authorization()
    def list_tests(self):
        return self._list_tests()

    # Submission Methods
    @auth.requires_authorization()
    def get_submission(self, uuid_hex):
        return self._get_submission(uuid_hex)
    @auth.requires_authorization()
    def list_submissions(self):
        return self._list_submissions()

    # Private User Methods
    def _create_user(self, data):
        return self.UserFactory.from_new(data)
    def _get_user(self, uuid_hex):
        return self.UserFactory.from_existing(uuid_hex)
    def _list_users(self):
        return self.UserFactory.list_siblings()

    # Private Group Methods
    def _create_group(self, data):
        return self.GroupFactory.from_new(data)
    def _get_group(self, uuid_hex):
        return self.GroupFactory.from_existing(uuid_hex)
    def _list_groups(self):
        return self.GroupFactory.list_siblings()

    # Private File Methods
    def _create_file(self, data, file_obj=None, dst=None, user=None):
        return self.FileFactory.from_new(data, file_obj=file_obj, dst=dst, user=user)
    def _get_file(self, uuid_hex):
        return self.FileFactory.from_existing(uuid_hex)
    def _list_files(self):
        return self.FileFactory.list_siblings()

    # Private Assignment Methods
    def _create_assignment(self, data, user=None):
        return self.AssignmentFactory.from_new(data, user=user)
    def _get_assignment(self, uuid_hex):
        return self.AssignmentFactory.from_existing(uuid_hex)
    def _list_assignments(self):
        return self.AssignmentFactory.list_siblings()

    # Private Test Methods
    def _get_test(self, uuid_hex):
        return self.TestFactory.from_existing(uuid_hex)
    def _list_tests(self):
        return self.TestFactory.list_siblings()

    # Private Submission Methods
    def _get_submission(self, uuid_hex):
        return self.SubmissionFactory.from_existing(uuid_hex)
    def _list_submissions(self):
        return self.SubmissionFactory.list_siblings()


### COGS Base Objects ###

## Authorized TSHashBase ##
class AuthTSHashBase(auth.AuthorizationMgmtMixin, backend.TSHashBase):

    # Public Methods
    @auth.requires_authorization()
    def update(self, data):
        return self._update(data)
    @auth.requires_authorization()
    def delete(self):
        return self._delete()

    # Private Methods
    def _update(self, data):
        return super(AuthTSHashBase, self).set_dict(data)
    def _delete(self):
        return super(AuthTSHashBase, self).delete()


## Authorized OwnedTSHashBase ##
class AuthOwnedTSHashBase(auth.AuthorizationMgmtMixin, backend.OwnedTSHashBase):

    # Public Methods
    @auth.requires_authorization()
    def update(self, data):
        return self._update(data)
    @auth.requires_authorization()
    def delete(self):
        return self._delete()

    # Private Methods
    def _update(self, data):
        return super(AuthOwnedTSHashBase, self).set_dict(data)
    def _delete(self):
        return super(AuthOwnedTSHashBase, self).delete()


## User Account Object ##
class UserBase(AuthTSHashBase):
    """COGS User Class"""
    schema = set(_TS_SCHEMA + _USER_SCHEMA)


## User List Object ##
class UserListBase(backend.SetBase):
    """COGS User List Class"""
    pass


## User Group Object ##
class GroupBase(AuthTSHashBase):
    """COGS Group Class"""

    schema = set(_TS_SCHEMA + _GROUP_SCHEMA)

    # Override Constructor
    def __init__(self, uuid_obj):
        """Base Constructor"""

        # Call Parent Construtor
        super(GroupBase, self).__init__(uuid_obj)

        # Setup Lists
        sf = backend.Factory(UserListBase, prefix=self.full_key, db=self.db, srv=self.srv)
        self.members = sf.from_raw('members')

    # Override Delete
    def _delete(self):
        if self.members.exists():
            self.members.delete()
        super(GroupBase, self)._delete()

    # Members Methods
    @auth.requires_authorization()
    def add_users(self, user_uuids):
        return self._add_users(user_uuids)
    @auth.requires_authorization()
    def rem_users(self, user_uuids):
        return self._rem_users(user_uuids)
    @auth.requires_authorization()
    def list_users(self):
        return self._list_users()

    # Private Members Methods
    def _add_users(self, user_uuids):
        return self.members.add_vals(user_uuids)
    def _rem_users(self, user_uuids):
        return self.members.del_vals(user_uuids)
    def _list_users(self):
        return self.members.get_set()


## Assignment Object ##
class AssignmentBase(AuthOwnedTSHashBase):
    """
    COGS Assignment Class

    """

    schema = set(_TS_SCHEMA + _ASSIGNMENT_SCHEMA)

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
    def _delete(self):

        # Remove Test Objects
        for tst_uuid in self._list_tests():
            tst = self.srv._get_test(tst_uuid)
            tst._delete()
        assert(not self._list_tests())

        # Remove Test List
        if self.tests.exists():
            self.tests.delete()

        # Remove Submission Objects
        for sub_uuid in self._list_submissions():
            sub = self.srv._get_submission(sub_uuid)
            sub._delete()
        assert(not self._list_submissions())

        # Remove Submission List
        if self.submissions.exists():
            self.submissions.delete()

        super(AssignmentBase, self)._delete()

    # Public Test Methods
    @auth.requires_authorization(pass_user=True)
    def create_test(self, dictionary, user=None):
        tst = self.srv.TestFactory.from_new(dictionary, asn=self, user=user)
        self._add_tests([str(tst.uuid)])
        return tst
    @auth.requires_authorization()
    def list_tests(self):
        return self._list_tests()

    # Public Submission Methods
    @auth.requires_authorization(pass_user=True)
    def create_submission(self, dictionary, user=None):
        sub = self.srv.SubmissionFactory.from_new(dictionary, asn=self, user=user)
        self._add_submissions([str(sub.uuid)])
        return sub
    @auth.requires_authorization()
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
class TestBase(AuthOwnedTSHashBase):
    """COGS Test Class"""

    schema = set(_TS_SCHEMA + _TEST_SCHEMA)

    # Override Constructor
    def __init__(self, uuid_obj):
        """Base Constructor"""

        # Call Parent Construtor
        super(TestBase, self).__init__(uuid_obj)

        # Setup Lists
        FileListFactory = backend.Factory(FileListBase, prefix=self.full_key, db=self.db, srv=self.srv)
        self.files = FileListFactory.from_raw('files')

    # Override Delete
    def _delete(self):

        # Remove from assignment
        tst_uuid = str(self.uuid)
        asn_uuid = self['assignment']
        if asn_uuid:
            asn = self.srv._get_assignment(asn_uuid)
            if not asn._rem_tests([tst_uuid]):
                msg = "Could not remove Test {:s} from Assignment {:s}".format(tst_uuid, asn_uuid)
                raise backend.ObjectError(msg)

        # Remove file list
        if self.files.exists():
            self.files.delete()

        # Call Parent
        super(TestBase, self)._delete()

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
    @auth.requires_authorization()
    def add_files(self, file_uuids):
        return self._add_files(file_uuids)
    @auth.requires_authorization()
    def rem_files(self, file_uuids):
        return self._rem_files(file_uuids)
    @auth.requires_authorization()
    def list_files(self):
        return self._list_files()

    # Private Files Methods
    def _add_files(self, file_uuids):
        return self.files.add_vals(file_uuids)
    def _rem_files(self, file_uuids):
        return self.files.del_vals(file_uuids)
    def _list_files(self):
        return self.files.get_set()


## Test List Object ##
class TestListBase(backend.SetBase):
    """COGS Test List Class"""
    pass


## Submission Object ##
class SubmissionBase(AuthOwnedTSHashBase):
    """COGS Submission Class"""

    schema = set(_TS_SCHEMA + _SUBMISSION_SCHEMA)

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
    def _delete(self):

        # Remove from assignment
        sub_uuid = str(self.uuid)
        asn_uuid = self['assignment']
        if asn_uuid:
            asn = self.srv._get_assignment(asn_uuid)
            if not asn._rem_submissions([sub_uuid]):
                msg = "Could not remove Submission {:s} from Assignment {:s}".format(sub_uuid, asn_uuid)
                raise backend.ObjectError(msg)

        # Remove run objects
        for run_uuid in self._list_runs():
            run = self.srv._get_runs(run_uuid)
            run._delete()
        assert(not self._list_runs())

        # Remove run list
        if self.runs.exists():
            self.runs.delete()

        # Remove file list
        if self.files.exists():
            self.files.delete()

        # Call Parent
        super(SubmissionBase, self)._delete()

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
    @auth.requires_authorization()
    def add_files(self, file_uuids):
        return self._add_files(file_uuids)
    @auth.requires_authorization()
    def rem_files(self, file_uuids):
        return self._rem_files(file_uuids)
    @auth.requires_authorization()
    def list_files(self):
        return self._list_files()

    # Run Methods
    @auth.requires_authorization(pass_user=True)
    def execute_run(self, tst, user=None):
        run = self.srv.RunFactory.from_new(tst, self, user=user)
        self._add_runs([str(run.uuid)])
        return run
    @auth.requires_authorization()
    def list_runs(self):
        return self._list_runs()

    # Private Files Methods
    def _add_files(self, file_uuids):
        return self.files.add_vals(file_uuids)
    def _rem_files(self, file_uuids):
        return self.files.del_vals(file_uuids)
    def _list_files(self):
        return self.files.get_set()

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
class RunBase(AuthOwnedTSHashBase):
    """COGS Run Class"""

    schema = set(_TS_SCHEMA + _RUN_SCHEMA)

    # Override from_new
    @classmethod
    def from_new(cls, tst, sub, **kwargs):
        """New Constructor"""

        # Create New Object
        data = {}

        # Setup Dict
        data['submission'] = str(sub.uuid)
        data['test'] = str(tst.uuid)
        data['status'] = ""
        data['score'] = ""
        data['output'] = ""

        # Create Run
        run = super(RunBase, cls).from_new(data, **kwargs)

        # Get Files
        tst_fls = tst._get_files()
        sub_fls = sub._get_files()

        # Grade Run
        env = environment.Env(run, tst_fls, sub_fls)
        tester = tester_script.Tester(env)
        ret, score, output = tester.test()
        env.close()

        # Set Results
        run['status'] = str(ret)
        run['score'] = str(score)
        run['output'] = str(output)

        # Return Run
        return run

    # Override Delete
    def _delete(self):

        # Remove from submission
        run_uuid = str(self.uuid)
        sub_uuid = self['submission']
        if sub_uuid:
            sub = self.srv._get_submission(sub_uuid)
            if not sub._rem_run([run_uuid]):
                msg = "Could not remove Run {:s} from Submission {:s}".format(run_uuid, sub_uuid)
                raise backend.ObjectError(msg)

        # Remove run objects
        for run_uuid in self._list_runs():
            run = self.srv._get_runs(run_uuid)
            run._delete()
        assert(not self._list_runs())

        # Remove run list
        if self.runs.exists():
            self.runs.delete()

        # Remove file list
        if self.files.exists():
            self.files.delete()

        # Call Parent
        super(SubmissionBase, self)._delete()


## Run List Object ##
class RunListBase(backend.SetBase):
    """COGS Run List Class"""
    pass


## File Object ##
class FileBase(AuthOwnedTSHashBase):
    """COGS File Class"""

    schema = set(_TS_SCHEMA + _FILE_SCHEMA)

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
    def _delete(self, force=False):
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
        super(FileBase, self)._delete()


## File List Object ##
class FileListBase(backend.SetBase):
    """COGS File List Class"""
    pass
