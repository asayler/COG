#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

# pylint: disable=no-name-in-module

### Imports ###
import time
import os
import uuid
import multiprocessing
import functools
import sys

import flask
import flask.ext.httpauth
import flask.ext.cors

import redis

import git

import cogs.config
import cogs.auth
import cogs.structs
import cogs.util

import perms


### Constants ###

_USERS_KEY = "users"
_USERNAME_KEY = "username"
_USERUUID_KEY = "useruuid"
_ADMINS_KEY = "admins"
_FILES_KEY = "files"
_REPORTERS_KEY = "reporters"
_ASSIGNMENTS_KEY = "assignments"
_TESTS_KEY = "tests"
_SUBMISSIONS_KEY = "submissions"
_RUNS_KEY = "runs"
_TOKENS_KEY = "tokens"
_TOKEN_KEY = "token"
_EXTRACT_KEY = "extract"


### Global Setup ###

app = flask.Flask(__name__)
app.config['JSON_AS_ASCII'] = False
cors = flask.ext.cors.CORS(app, headers=["Content-Type", "Authorization"])
httpauth = flask.ext.httpauth.HTTPBasicAuth()
srv = cogs.structs.Server()
auth = cogs.auth.Auth()


### Logging ###

if cogs.config.LOGGING_ENABLED:

    import logging
    import logging.handlers

    loggers = [app.logger, perms.logger, logging.getLogger('cogs')]

    formatter_line = logging.Formatter('%(levelname)s: %(module)s - %(message)s')
    formatter_line_time = logging.Formatter('%(asctime)s %(levelname)s: %(module)s - %(message)s')

    # Stream Handler
    handler_stream = logging.StreamHandler()
    handler_stream.setFormatter(formatter_line)
    if app.debug:
        handler_stream.setLevel(logging.DEBUG)
    else:
        handler_stream.setLevel(logging.WARNING)

    # File Handler
    if not os.path.exists(cogs.config.LOGGING_PATH):
        os.makedirs(cogs.config.LOGGING_PATH)
    logfile_path = "{:s}/{:s}".format(cogs.config.LOGGING_PATH, "api.log")
    handler_file = logging.handlers.WatchedFileHandler(logfile_path)
    handler_file.setFormatter(formatter_line_time)
    if app.debug:
        handler_file.setLevel(logging.DEBUG)
    else:
        handler_file.setLevel(logging.INFO)

    for logger in loggers:
        if app.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        logger.addHandler(handler_stream)
        logger.addHandler(handler_file)


### Functions ###

## Authentication Functions ##

@httpauth.verify_password
def verify_login(username, password):

    app.logger.debug("verify_login: username={}".format(username))

    flask.g.user = None

    # Username:Password Case
    if password:
        user = auth.auth_userpass(username, password)
        if user:
            flask.g.user = user
            return True
        elif user == False:
            return False
        else:
            try:
                user = auth.create_user({}, username=username, password=password)
            except cogs.auth.BadCredentialsError:
                return False
            else:
                flask.g.user = user
                return True
    # Token Case
    else:
        user = auth.auth_token(username)
        if user:
            flask.g.user = user
            return True
        else:
            return False


def get_owner(func_get):

    def _decorator(func):

        @functools.wraps(func)
        def _wrapper(*args, **kwargs):

            # Get UUID
            obj_uuid = kwargs['obj_uuid']

            # Get Object
            obj = func_get(obj_uuid)

            # Get Owner
            flask.g.owner = obj.get('owner', None)

            # Call Function
            return func(*args, **kwargs)

        return _wrapper

    return _decorator

## Helper Functions ##

def save_upload(file_obj):

    upload_dir = os.path.abspath(cogs.config.UPLOAD_PATH)
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    upload_uuid = uuid.uuid4()
    upload_path = os.path.abspath("{:s}/{:s}".format(upload_dir, upload_uuid))
    file_obj.save(upload_path)
    file_obj.close()
    return upload_path

def error_response(e, status):

    err = { 'status': status,
            'message': str(e) }
    err_res = flask.jsonify(err)
    err_res.status_code = err['status']
    return err_res

def create_stub_json(func_create, **kwargs):

    data = flask.request.get_json(force=True)
    obj = func_create(data, owner=flask.g.user, **kwargs)
    obj_lst = list([str(obj.uuid)])
    return obj_lst

def create_stub_file(func_create, files=[]):

    obj_lst = []
    for file_obj in files:

        # Process upload
        data = {}
        data['key'] = file_obj.name
        data['name'] = file_obj.filename
        src_path = save_upload(file_obj)

        # Create File
        obj = func_create(data, src_path=src_path, owner=flask.g.user)
        obj_lst.append(str(obj.uuid))

        # Cleanup
        os.remove(src_path)

    return obj_lst

def create_stub_files(func_create, files=[]):

    obj_lst = []
    for archive_obj in files:

        # Process upload
        data = {}
        data['key'] = archive_obj.name
        data['name'] = archive_obj.filename
        archive_src_path = save_upload(archive_obj)

        # Create Files
        objs = func_create(data, archive_src_path=archive_src_path, owner=flask.g.user)
        for obj in objs:
            obj_lst.append(str(obj.uuid))

        # Cleanup
        os.remove(archive_src_path)

    return obj_lst

def update_stub_json(obj):

    data = flask.request.get_json(force=True)
    obj.set_dict(data)
    obj_dict = obj.get_dict()
    return obj_dict

def process_objects(func_list, func_create,
                    func_filter=None, create_stub=create_stub_json, **kwargs):

    # List Objects
    if flask.request.method == 'GET':
        obj_lst = list(func_list())

    # Create Object
    elif flask.request.method == 'POST':
        obj_lst = create_stub(func_create, **kwargs)

    # Bad Method
    else:
        raise Exception("Unhandled Method")

    # Filter List
    if func_filter:
        obj_lst = func_filter(obj_lst)

    # Return Object List
    return obj_lst

def process_object(func_get, obj_uuid, update_stub=update_stub_json, raw=False):

    # Get Object
    obj = func_get(obj_uuid)

    # Get Object Data
    if flask.request.method == 'GET':
        obj_dict = obj.get_dict()

    # Update Object Data
    elif flask.request.method == 'PUT':
        obj_dict = update_stub(obj)

    # Delete Object
    elif flask.request.method == 'DELETE':
        obj_dict = obj.get_dict()
        obj.delete()

    # Bad Method
    else:
        raise Exception("Unhandled Method")

    # Return Object
    if raw:
        return obj_dict
    else:
        out = {str(obj.uuid): obj_dict}
        return flask.jsonify(out)

def process_uuid_list(func_list, func_add, func_remove, key):

    # Sanitize Input
    def sanitize_uuid_list(in_lst):
        out_lst = []
        for in_uuid in in_lst:
            out_uuid = str(uuid.UUID(in_uuid))
            out_lst.append(out_uuid)
        return out_lst

    # List Objects
    if flask.request.method == 'GET':

        out_lst = list(func_list())

    # Add Objects
    elif flask.request.method == 'PUT':
        in_obj = flask.request.get_json(force=True)
        in_lst = list(in_obj[key])
        add_lst = sanitize_uuid_list(in_lst)
        func_add(add_lst)
        out_lst = list(func_list())

    # Remove Objects
    elif flask.request.method == 'DELETE':
        in_obj = flask.request.get_json(force=True)
        in_lst = list(in_obj[key])
        rem_lst = sanitize_uuid_list(in_lst)
        func_remove(rem_lst)
        out_lst = list(func_list())

    # Bad Method
    else:
        raise Exception("Unhandled Method")

    # Return Object List

    out_obj = {key: out_lst}
    return flask.jsonify(out_obj)


## Filter Functions ##

def filter_asns_submitable(asn_list):

    asns_submitable = []

    for asn_uuid in asn_list:
        asn = srv.get_assignment(asn_uuid)
        if int(asn['accepting_submissions']):
            if int(asn['respect_duedate']):
                if asn['duedate']:
                    time_due = float(asn["duedate"])
                else:
                    time_due = 0
                    app.logger.warn("Assignment {:s} set to respect duedate, ".format(asn) +
                                    "but no duedate provided")
                time_now = time.time()
                if (time_now < time_due):
                    asns_submitable.append(asn_uuid)
            else:
                asns_submitable.append(asn_uuid)

    return asns_submitable

def filter_asns_runable(asn_list):

    asns_runable = []

    for asn_uuid in asn_list:
        asn = srv.get_assignment(asn_uuid)
        if int(asn['accepting_runs']):
            asns_runable.append(asn_uuid)

    return asns_runable


### Endpoints ###

## Root Endpoints ##

@app.route("/", methods=['GET'])
def get_root():

    app.logger.debug("GET ROOT")
    try:
        repo = git.Repo(cogs.config.ROOT_PATH)
    except git.exc.InvalidGitRepositoryError as err:
        return flask.render_template('index.html', branch="None",
                                     shorthash="None", longhash="")
    else:
        try:
            branch = str(repo.active_branch)
        except TypeError as err:
            branch = "Detached"
        commit = repo.commit()
        longhash = str(commit)
        shorthash = longhash[0:7]
        return flask.render_template('index.html', branch=branch,
                                     shorthash=shorthash, longhash=longhash)

## Access Control Endpoints ##

@app.route("/my/{}/".format(_TOKEN_KEY), methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def my_token():
    token = flask.g.user['token']
    out = {_TOKEN_KEY: token}
    return flask.jsonify(out)

@app.route("/my/{}/".format(_USERNAME_KEY), methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def my_username():
    username = flask.g.user['username']
    out = {_USERNAME_KEY: username}
    return flask.jsonify(out)

@app.route("/my/{}/".format(_USERUUID_KEY), methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def my_useruuid():
    useruuid = str(flask.g.user.uuid)
    out = {_USERUUID_KEY: useruuid}
    return flask.jsonify(out)

@app.route("/{}/".format(_USERS_KEY), methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def list_users():
    uid_lst = process_objects(auth.list_users, None)
    out = {_USERS_KEY: uid_lst}
    return flask.jsonify(out)

@app.route("/{}/<obj_uuid>/".format(_USERS_KEY), methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def process_user(obj_uuid):
    return process_object(auth.get_user, obj_uuid)

@app.route("/{}/{}/<username>/".format(_USERS_KEY, _USERUUID_KEY), methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def user_to_uuid(username):
    useruuid = auth.username_map.lookup_username(username)
    out = {_USERUUID_KEY: useruuid}
    return flask.jsonify(out)

@app.route("/{}/{}/<useruuid>/".format(_USERS_KEY, _USERNAME_KEY), methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def uuid_to_user(useruuid):
    username = auth.get_user(useruuid)['username']
    out = {_USERNAME_KEY: username}
    return flask.jsonify(out)

@app.route("/{}/".format(_ADMINS_KEY), methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def process_admins():
    return process_uuid_list(auth.list_admins, None, None, _ADMINS_KEY)

## File Endpoints ##

@app.route("/{}/".format(_FILES_KEY), methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def process_files_get():

    app.logger.debug("LIST FILES")
    uid_lst = process_objects(srv.list_files, None, create_stub=None)
    out = {_FILES_KEY: uid_lst}
    return flask.jsonify(out)

@app.route("/{}/".format(_FILES_KEY), methods=['POST'])
@httpauth.login_required
@auth.requires_auth_route()
def process_files_post():

    app.logger.debug("POST FILES")

    files = flask.request.files
    files_extract = []
    files_direct = []
    for key in files:

        if key == _EXTRACT_KEY:
            files_extract += files.getlist(key)
        else:
            files_direct += files.getlist(key)

    uid_lst = []
    if files_extract:
        uid_lst += process_objects(None, srv.create_files,
                                   create_stub=create_stub_files, files=files_extract)
    if files_direct:
        uid_lst += process_objects(None, srv.create_file,
                                   create_stub=create_stub_file, files=files_direct)

    if flask.request.method == 'POST':
        perms.create_perms(uid_lst, _FILES_KEY)
    out = {_FILES_KEY: uid_lst}
    return flask.jsonify(out)

@app.route("/{}/<obj_uuid>/".format(_FILES_KEY), methods=['GET', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_file)
@auth.requires_auth_route()
def process_file(obj_uuid):
    return process_object(srv.get_file, obj_uuid, update_stub=None)

@app.route("/{}/<obj_uuid>/contents/".format(_FILES_KEY), methods=['GET'])
@httpauth.login_required
@get_owner(srv.get_file)
@auth.requires_auth_route()
def process_file_contents(obj_uuid):

    # Serve File Contents
    file_dict = process_object(srv.get_file, obj_uuid, update_stub=None, raw=True)
    file_path = file_dict['path']
    file_name = cogs.util.clean_path(os.path.basename(file_dict['name']))
    return flask.send_file(file_path, as_attachment=True, attachment_filename=file_name)

## Reporter Endpoints ##

@app.route("/{}/".format(_REPORTERS_KEY), methods=['GET', 'POST'])
@httpauth.login_required
@auth.requires_auth_route()
def process_reporters():
    uid_lst = process_objects(srv.list_reporters, srv.create_reporter)
    if flask.request.method == 'POST':
        perms.create_perms(uid_lst, _REPORTERS_KEY)
    out = {_REPORTERS_KEY: uid_lst}
    return flask.jsonify(out)

@app.route("/{}/<obj_uuid>/".format(_REPORTERS_KEY), methods=['GET', 'PUT', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_reporter)
@auth.requires_auth_route()
def process_reporter(obj_uuid):
    return process_object(srv.get_reporter, obj_uuid)

## Assignment Endpoints ##

@app.route("/{}/".format(_ASSIGNMENTS_KEY), methods=['GET', 'POST'])
@httpauth.login_required
@auth.requires_auth_route()
def process_assignments():
    uid_lst = process_objects(srv.list_assignments, srv.create_assignment)
    if flask.request.method == 'POST':
        perms.create_perms(uid_lst, _ASSIGNMENTS_KEY)
    out = {_ASSIGNMENTS_KEY: uid_lst}
    return flask.jsonify(out)

@app.route("/{}/submitable/".format(_ASSIGNMENTS_KEY), methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def process_assignments_submitable():
    uid_lst = process_objects(srv.list_assignments, None,
                              func_filter=filter_asns_submitable)
    out = {_ASSIGNMENTS_KEY: uid_lst}
    return flask.jsonify(out)

@app.route("/{}/runable/".format(_ASSIGNMENTS_KEY), methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def process_assignments_runable():
    uid_lst = process_objects(srv.list_assignments, None,
                              func_filter=filter_asns_runable)
    out = {_ASSIGNMENTS_KEY: uid_lst}
    return flask.jsonify(out)

@app.route("/{}/<obj_uuid>/".format(_ASSIGNMENTS_KEY), methods=['GET', 'PUT', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_assignment)
@auth.requires_auth_route()
def process_assignment(obj_uuid):
    return process_object(srv.get_assignment, obj_uuid)

@app.route("/{}/<obj_uuid>/tests/".format(_ASSIGNMENTS_KEY), methods=['GET', 'POST'])
@httpauth.login_required
@get_owner(srv.get_assignment)
@auth.requires_auth_route()
def process_assignment_tests(obj_uuid):

    # Get Assignment
    asn = srv.get_assignment(obj_uuid)

    # Process Tests
    uid_lst = process_objects(asn.list_tests, asn.create_test)
    if flask.request.method == 'POST':
        perms.create_perms(uid_lst, _TESTS_KEY)
    out = {_TESTS_KEY: uid_lst}
    return flask.jsonify(out)

@app.route("/{}/<obj_uuid>/submissions/".format(_ASSIGNMENTS_KEY), methods=['GET', 'POST'])
@httpauth.login_required
@get_owner(srv.get_assignment)
@auth.requires_auth_route()
def process_assignment_submissions(obj_uuid):

    # Get Assignment
    asn = srv.get_assignment(obj_uuid)

    # Process Submissions
    uid_lst = process_objects(asn.list_submissions, asn.create_submission)
    if flask.request.method == 'POST':
        perms.create_perms(uid_lst, _SUBMISSIONS_KEY)
    out = {_SUBMISSIONS_KEY: uid_lst}
    return flask.jsonify(out)

## Test Endpoints ##

@app.route("/{}/".format(_TESTS_KEY), methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def process_tests():
    uid_lst = process_objects(srv.list_tests, None)
    out = {_TESTS_KEY: uid_lst}
    return flask.jsonify(out)

@app.route("/{}/<obj_uuid>/".format(_TESTS_KEY), methods=['GET', 'PUT', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_test)
@auth.requires_auth_route()
def process_test(obj_uuid):
    return process_object(srv.get_test, obj_uuid)

@app.route("/{}/<obj_uuid>/files/".format(_TESTS_KEY), methods=['GET', 'PUT', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_test)
@auth.requires_auth_route()
def process_test_files(obj_uuid):

    # Get Test
    tst = srv.get_test(obj_uuid)

    # Process Files
    return process_uuid_list(tst.list_files, tst.add_files, tst.rem_files, _FILES_KEY)

@app.route("/{}/<obj_uuid>/reporters/".format(_TESTS_KEY), methods=['GET', 'PUT', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_test)
@auth.requires_auth_route()
def process_test_reporters(obj_uuid):

    # Get Test
    tst = srv.get_test(obj_uuid)

    # Process Reporters
    return process_uuid_list(tst.list_reporters, tst.add_reporters, tst.rem_reporters, _REPORTERS_KEY)

## Submission Endpoints ##

@app.route("/{}/".format(_SUBMISSIONS_KEY), methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def process_submissions():
    uid_lst = process_objects(srv.list_submissions, None)
    out = {_SUBMISSIONS_KEY: uid_lst}
    return flask.jsonify(out)

@app.route("/{}/<obj_uuid>/".format(_SUBMISSIONS_KEY), methods=['GET', 'PUT', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_submission)
@auth.requires_auth_route()
def process_submission(obj_uuid):
    return process_object(srv.get_submission, obj_uuid)

@app.route("/{}/<obj_uuid>/files/".format(_SUBMISSIONS_KEY), methods=['GET', 'PUT', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_submission)
@auth.requires_auth_route()
def process_submission_files(obj_uuid):

    # Get Submission
    sub = srv.get_submission(obj_uuid)

    # Process Files
    return process_uuid_list(sub.list_files, sub.add_files, sub.rem_files, _FILES_KEY)

@app.route("/{}/<obj_uuid>/runs/".format(_SUBMISSIONS_KEY), methods=['GET', 'POST'])
@httpauth.login_required
@get_owner(srv.get_submission)
@auth.requires_auth_route()
def process_submission_runs(obj_uuid):

    # Get Submission
    sub = srv.get_submission(obj_uuid)

    # Process Runs
    uid_lst = process_objects(sub.list_runs, sub.execute_run)
    if flask.request.method == 'POST':
        perms.create_perms(uid_lst, _RUNS_KEY)
    out = {_RUNS_KEY: uid_lst}
    return flask.jsonify(out)

## Run Endpoints ##

@app.route("/{}/".format(_RUNS_KEY), methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def process_runs():
    uid_lst = process_objects(srv.list_runs, None)
    out = {_RUNS_KEY: uid_lst}
    return flask.jsonify(out)

@app.route("/{}/<obj_uuid>/".format(_RUNS_KEY), methods=['GET', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_run)
@auth.requires_auth_route()
def process_run(obj_uuid):
    return process_object(srv.get_run, obj_uuid)


### Exceptions ###

@app.errorhandler(cogs.auth.UserNotAuthorizedError)
def not_authorized(error):
    err = { 'status': 401,
            'message': str(error) }
    app.logger.info("Client Error: UserNotAuthorized: {:s}".format(err))
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

@app.errorhandler(cogs.structs.ObjectDNE)
def object_not_found(error=False):
    err = { 'status': 404,
            'message': "Not Found: {:s}".format(flask.request.url) }
    app.logger.info("Client Error: ObjectDNE: {:s}".format(err))
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

@app.errorhandler(KeyError)
def bad_key(error):
    err = { 'status': 400,
            'message': "{:s}".format(error) }
    app.logger.info("Client Error: KeyError: {:s}".format(err))
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

@app.errorhandler(ValueError)
def bad_value(error):
    err = { 'status': 400,
            'message': "{:s}".format(error) }
    app.logger.info("Client Error: ValueError: {:s}".format(err))
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

@app.errorhandler(TypeError)
def bad_type(error):
    err = { 'status': 400,
            'message': "{:s}".format(error) }
    app.logger.info("Client Error: TypeError: {:s}".format(err))
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

@app.errorhandler(400)
def bad_request(error=False):
    err = { 'status': 400,
            'message': "Malformed request" }
    app.logger.info("Client Error: 400: {:s}".format(err))
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

@app.errorhandler(401)
def not_authorized_401(error=False):
    err = { 'status': 401,
            'message': "Not Authorized" }
    app.logger.info("Client Error: 401: {:s}".format(err))
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

@app.errorhandler(404)
def not_found(error=False):
    err = { 'status': 404,
            'message': "Not Found: {:s}".format(flask.request.url) }
    app.logger.info("Client Error: 404: {:s}".format(err))
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

@app.errorhandler(405)
def bad_method(error=False):
    err = { 'status': 405,
            'message': "Bad Method: {:s} {:s}".format(flask.request.method, flask.request.url) }
    app.logger.info("Client Error: 405: {:s}".format(err))
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

### Run Test Server ###

if __name__ == "__main__":
    app.run(debug=True)
