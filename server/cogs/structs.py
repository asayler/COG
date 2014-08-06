# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado


import backend_redis as backend
from backend_redis import BackendError, FactoryError, ObjectError, ObjectDNE


_TS_SCHEMA = ['created_time', 'modified_time']
_USER_SCHEMA = ['username', 'first', 'last', 'type']
_GROUP_SCHEMA = ['name', 'members']
_COL_PERMISSION_SCHEMA = ['create', 'list']
_OBJ_PERMISSION_SCHEMA = ['read', 'write', 'delete']
_ASSIGNMENT_SCHEMA = ['name', 'contact', 'permissions']
_TEST_SCHEMA = ['name', 'contact', 'type', 'maxscore']
_SUBMISSION_SCHEMA = ['author']
_RUN_SCHEMA = ['test', 'status', 'score', 'output']
_FILE_SCHEMA = ['key', 'name', 'type', 'encoding', 'path']

_FILES_DIR = "./files/"


### COGS Core Objects ###

## Top-Level Server Object ##
class Server(object):
    """
    COGS Server Class

    """

    # Override Constructor
    def __init__(self, db=None):
        """Base Constructor"""

        # Call Parent Construtor
        super(Server, self).__init__()

        # Setup Factories
        self.AssignmentFactory = backend.UUIDFactory(AssignmentBase, db=db)
        self.UserFactory = backend.UUIDFactory(UserBase, db=db)

    # Assignment Methods
    def create_assignment(self, d):
        return self.AssignmentFactory.from_new(d)
    def get_assignment(self, uuid_hex):
        return self.AssignmentFactory.from_existing(uuid_hex)
    def get_assignments(self):
        return self.AssignmentFactory.get_siblings()
    def list_assignments(self):
        return self.AssignmentFactory.list_siblings()

    # User Methods
    def create_user(self, d):
        return self.UserFactory.from_new(d)
    def get_user(self, uuid_hex):
        return self.UserFactory.from_existing(uuid_hex)
    def get_users(self):
        return self.UserFactory.get_siblings()
    def list_users(self):
        return self.UserFactory.list_siblings()


### COGS Base Objects ###

## User Account Object ##
class UserBase(backend.TSHashBase):
    """
    COGS User Class

    """

    schema = set(_TS_SCHEMA + _USER_SCHEMA)


## Assignment Object ##
class AssignmentBase(backend.TSHashBase):
    """
    COGS Assignment Class

    """

    schema = set(_TS_SCHEMA + _ASSIGNMENT_SCHEMA)

    # Override Constructor
    def __init__(self, uuid_obj):
        """Base Constructor"""

        # Call Parent Construtor
        super(AssignmentBase, self).__init__(uuid_obj)

        # Setup Factories
        self.TestFactory = backend.UUIDFactory(TestBase, prefix=self.full_key, db=self.db)
        self.SubmissionFactory = backend.UUIDFactory(SubmissionBase, prefix=self.full_key, db=self.db, )

    # Override Delete
    def delete(self):
        """Delete"""

        # Delete Tests
        for t_uuid in self.list_tests():
            tst = self.get_test(t_uuid)
            tst.delete()

        # Delete Submissions
        for s_uuid in self.list_submissions():
            sub = self.get_submission(s_uuid)
            sub.delete()

        # Delete Self
        super(AssignmentBase, self).delete()

    # Test Methods
    def create_test(self, d):
        return self.TestFactory.from_new(d)
    def get_test(self, uuid_hex):
        return self.TestFactory.from_existing(uuid_hex)
    def get_tests(self):
        return self.TestFactory.get_siblings()
    def list_tests(self):
        return self.TestFactory.list_siblings()

    # Submission Methods
    def create_submission(self, d):
        return self.SubmissionFactory.from_new(d)
    def get_submission(self, uuid_hex):
        return self.SubmissionFactory.from_existing(uuid_hex)
    def get_submissions(self):
        return self.SubmissionFactory.get_siblings()
    def list_submissions(self):
        return self.SubmissionFactory.list_siblings()


## Assignment Test Object ##
class TestBase(backend.TSHashBase):
    """
    COGS Test Class

    """

    schema = set(_TS_SCHEMA + _TEST_SCHEMA)

    # Override Constructor
    def __init__(self, uuid_obj):
        """Base Constructor"""
        super(TestBase, self).__init__(uuid_obj)
        self.FileFactory = backend.UUIDFactory(FileBase, prefix=self.full_key, db=self.db)

    # Override Delete
    def delete(self):
        """Delete"""

        # Delete Files
        for f_uuid in self.list_files():
            fle = self.get_file(f_uuid)
            fle.delete(force=True)

        # Delete Self
        super(TestBase, self).delete()

    # File Methods
    def create_file(self, d, file_obj):
        return self.FileFactory.from_new(d, file_obj)
    def get_file(self, uuid_hex):
        return self.FileFactory.from_existing(uuid_hex)
    def get_files(self):
        return self.FileFactory.get_siblings()
    def list_files(self):
        return self.FileFactory.list_siblings()


## Assignment Submission Object ##
class SubmissionBase(backend.TSHashBase):
    """
    COGS Submission Class

    """

    schema = set(_TS_SCHEMA + _SUBMISSION_SCHEMA)

    # Override Constructor
    def __init__(self, uuid_obj):
        """Base Constructor"""
        super(SubmissionBase, self).__init__(uuid_obj)
        self.FileFactory = backend.UUIDFactory(FileBase, prefix=self.full_key, db=self.db)
        self.RunFactory = backend.UUIDFactory(RunBase, prefix=self.full_key, db=self.db)

    # Override Delete
    def delete(self):
        """Delete"""

        # Delete Files
        for f_uuid in self.list_files():
            fle = self.get_file(f_uuid)
            fle.delete(force=True)

        # Delete Runs
        for r_uuid in self.list_runs():
            run = self.get_run(r_uuid)
            run.delete()

        # Delete Self
        super(Submission, self).delete()

    # File Methods
    def create_file(self, d, file_obj):
        return self.FileFactory.from_new(d, file_obj)
    def get_file(self, uuid_hex):
        return self.FileFactory.from_existing(uuid_hex)
    def get_files(self):
        return self.FileFactory.get_siblings()
    def list_files(self):
        return self.FileFactory.list_siblings()

    # Run Methods
    def execute_run(self, tst, sub):
        return self.RunFactory.from_new(tst, sub)
    def get_run(self, uuid_hex):
        return self.RunFactory.from_existing(uuid_hex)
    def get_runs(self):
        return self.RunFactory.get_siblings()
    def list_runs(self):
        return self.RunFactory.list_siblings()


## Test Run Object ##
class RunBase(backend.TSHashBase):
    """
    COGS Run Class

    """

    schema = set(_TS_SCHEMA + _RUN_SCHEMA)

    # Override from_new
    @classmethod
    def from_new(cls, tst, sub):
        """New Constructor"""

        # Create New Object
        data = {}

        # Setup Dict
        data['test'] = repr(tst)
        data['status'] = ""
        data['score'] = ""
        data['output'] = ""

        # Create Run
        run = super(RunBase, cls).from_new(data)

        # Get Files
        tst_fls = tst.get_files()
        sub_fls = sub.get_files()

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


## File Object ##
class FileBase(backend.TSHashBase):
    """
    COGS File Class

    """

    schema = set(_TS_SCHEMA + _FILE_SCHEMA)

    # Override from_new
    @classmethod
    def from_new(cls, d, file_obj=None, dst=None):
        """New Constructor"""

        # Create New Object
        data = copy.deepcopy(d)

        # Setup file_obj
        if file_obj is None:
            src_path = os.path.abspath("{:s}".format(data['path']))
            src_file = open(src_path, 'rb')
            file_obj = werkzeug.datastructures.FileStorage(stream=src_file, filename=data['name'])
        else:
            data['name'] = str(file_obj.filename)
            data['path'] = ""

        # Get Type
        typ = mimetypes.guess_type(file_obj.filename)
        data['type'] = str(typ[0])
        data['encoding'] = str(typ[1])

        # Create File
        fle = super(FileBase, cls).from_new(data)

        # Set Path
        if dst is None:
            fle['path'] = os.path.abspath("{:s}/{:s}".format(_FILES_DIR, repr(fle)))
        else:
            fle['path'] = os.path.abspath("{:s}".format(dst))

        # Save File
        try:
            file_obj.save(fle['path'])
            file_obj.close()
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
        super(FileBase, self).delete()