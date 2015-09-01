#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

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

import cogs.config

import cogs.auth
import cogs.structs


### Constants ###

_FILES_KEY = "files"
_REPORTERS_KEY = "reporters"
_ASSIGNMENTS_KEY = "assignments"
_TESTS_KEY = "tests"
_SUBMISSIONS_KEY = "submissions"
_RUNS_KEY = "runs"
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

    loggers = [app.logger, logging.getLogger('cogs')]

    formatter_line = logging.Formatter('%(levelname)s: %(module)s - %(message)s')
    formatter_line_time = logging.Formatter('%(asctime)s %(levelname)s: %(module)s - %(message)s')

    # Stream Handler
    handler_stream = logging.StreamHandler()
    handler_stream.setFormatter(formatter_line)
    handler_stream.setLevel(logging.WARNING)

    # File Handler
    if not os.path.exists(cogs.config.LOGGING_PATH):
        os.makedirs(cogs.config.LOGGING_PATH)
    logfile_path = "{:s}/{:s}".format(cogs.config.LOGGING_PATH, "api.log")
    handler_file = logging.handlers.WatchedFileHandler(logfile_path)
    handler_file.setFormatter(formatter_line_time)
    handler_file.setLevel(logging.INFO)

    for logger in loggers:
        logger.addHandler(handler_stream)
        logger.addHandler(handler_file)


### Functions ###

## Authentication Functions ##

@httpauth.verify_password
def verify_login(username, password):

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

def process_objects(func_list, func_create, key,
                    func_filter=None, create_stub=create_stub_json, raw=False, **kwargs):

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
    if raw:
        return obj_lst
    else:
        out = {key: obj_lst}
        return flask.jsonify(out)

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

    return app.send_static_file('index.html')

## Access Control Endpoints ##

@app.route("/tokens/", methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def get_token():

    # Get Token
    token = flask.g.user['token']

    # Return Token
    out = {str(_TOKEN_KEY): str(token)}
    return flask.jsonify(out)

# ToDo: User and Group Control

## File Endpoints ##

@app.route("/files/", methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def process_files_get():
    return process_objects(srv.list_files, None, _FILES_KEY, create_stub=None)

@app.route("/files/", methods=['POST'])
@httpauth.login_required
@auth.requires_auth_route()
def process_files_post():

    files = flask.request.files
    files_extract = []
    files_direct = []
    for key in files:

        if key == _EXTRACT_KEY:
            files_extract += files.getlist(key)
        else:
            files_direct += files.getlist(key)

    obj_lst = []
    if files_extract:
        obj_lst += process_objects(None, srv.create_files, _FILES_KEY,
                                   create_stub=create_stub_files, raw=True, files=files_extract)
    if files_direct:
        obj_lst += process_objects(None, srv.create_file, _FILES_KEY,
                                   create_stub=create_stub_file, raw=True, files=files_direct)

    out = {_FILES_KEY: obj_lst}
    return flask.jsonify(out)

@app.route("/files/<obj_uuid>/", methods=['GET', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_file)
@auth.requires_auth_route()
def process_file(obj_uuid):
    return process_object(srv.get_file, obj_uuid, update_stub=None)

@app.route("/files/<obj_uuid>/contents/", methods=['GET'])
@httpauth.login_required
@get_owner(srv.get_file)
@auth.requires_auth_route()
def process_file_contents(obj_uuid):

    # Serve File Contents
    file_dict = process_object(srv.get_file, obj_uuid, update_stub=None, raw=True)
    file_path = file_dict['path']
    file_name = os.path.basename(file_dict['name'])
    return flask.send_file(file_path, as_attachment=True, attachment_filename=file_name)

## Reporter Endpoints ##

@app.route("/reporters/", methods=['GET', 'POST'])
@httpauth.login_required
@auth.requires_auth_route()
def process_reporters():
    return process_objects(srv.list_reporters, srv.create_reporter, _REPORTERS_KEY)

@app.route("/reporters/<obj_uuid>/", methods=['GET', 'PUT', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_reporter)
@auth.requires_auth_route()
def process_reporter(obj_uuid):
    return process_object(srv.get_reporter, obj_uuid)

## Assignment Endpoints ##

@app.route("/assignments/", methods=['GET', 'POST'])
@httpauth.login_required
@auth.requires_auth_route()
def process_assignments():
    return process_objects(srv.list_assignments, srv.create_assignment, _ASSIGNMENTS_KEY)

@app.route("/assignments/submitable/", methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def process_assignments_submitable():
    return process_objects(srv.list_assignments, None, _ASSIGNMENTS_KEY,
                           func_filter=filter_asns_submitable, create_stub=None)

@app.route("/assignments/runable/", methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def process_assignments_runable():
    return process_objects(srv.list_assignments, None, _ASSIGNMENTS_KEY,
                           func_filter=filter_asns_runable, create_stub=None)

@app.route("/assignments/<obj_uuid>/", methods=['GET', 'PUT', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_assignment)
@auth.requires_auth_route()
def process_assignment(obj_uuid):
    return process_object(srv.get_assignment, obj_uuid)

@app.route("/assignments/<obj_uuid>/tests/", methods=['GET', 'POST'])
@httpauth.login_required
@get_owner(srv.get_assignment)
@auth.requires_auth_route()
def process_assignment_tests(obj_uuid):

    # Get Assignment
    asn = srv.get_assignment(obj_uuid)

    # Process Tests
    return process_objects(asn.list_tests, asn.create_test, _TESTS_KEY)

@app.route("/assignments/<obj_uuid>/submissions/", methods=['GET', 'POST'])
@httpauth.login_required
@get_owner(srv.get_assignment)
@auth.requires_auth_route()
def process_assignment_submissions(obj_uuid):

    # Get Assignment
    asn = srv.get_assignment(obj_uuid)

    # Process Submissions
    return process_objects(asn.list_submissions, asn.create_submission, _SUBMISSIONS_KEY)

## Test Endpoints ##

@app.route("/tests/", methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def process_tests():
    return process_objects(srv.list_tests, None, _TESTS_KEY)

@app.route("/tests/<obj_uuid>/", methods=['GET', 'PUT', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_test)
@auth.requires_auth_route()
def process_test(obj_uuid):
    return process_object(srv.get_test, obj_uuid)

@app.route("/tests/<obj_uuid>/files/", methods=['GET', 'PUT', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_test)
@auth.requires_auth_route()
def process_test_files(obj_uuid):

    # Get Test
    tst = srv.get_test(obj_uuid)

    # Process Files
    return process_uuid_list(tst.list_files, tst.add_files, tst.rem_files, _FILES_KEY)

@app.route("/tests/<obj_uuid>/reporters/", methods=['GET', 'PUT', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_test)
@auth.requires_auth_route()
def process_test_reporters(obj_uuid):

    # Get Test
    tst = srv.get_test(obj_uuid)

    # Process Reporters
    return process_uuid_list(tst.list_reporters, tst.add_reporters, tst.rem_reporters, _REPORTERS_KEY)

## Submission Endpoints ##

@app.route("/submissions/", methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def process_submissions():
    return process_objects(srv.list_submissions, None, _SUBMISSIONS_KEY)

@app.route("/submissions/<obj_uuid>/", methods=['GET', 'PUT', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_submission)
@auth.requires_auth_route()
def process_submission(obj_uuid):
    return process_object(srv.get_submission, obj_uuid)

@app.route("/submissions/<obj_uuid>/files/", methods=['GET', 'PUT', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_submission)
@auth.requires_auth_route()
def process_submission_files(obj_uuid):

    # Get Submission
    sub = srv.get_submission(obj_uuid)

    # Process Files
    return process_uuid_list(sub.list_files, sub.add_files, sub.rem_files, _FILES_KEY)

@app.route("/submissions/<obj_uuid>/runs/", methods=['GET', 'POST'])
@httpauth.login_required
@get_owner(srv.get_submission)
@auth.requires_auth_route()
def process_submission_runs(obj_uuid):

    # Get Submission
    sub = srv.get_submission(obj_uuid)

    # Process Runs
    return process_objects(sub.list_runs, sub.execute_run, _RUNS_KEY)

## Run Endpoints ##

@app.route("/runs/", methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def process_runs():
    return process_objects(srv.list_runs, None, _RUNS_KEY)

@app.route("/runs/<obj_uuid>/", methods=['GET', 'DELETE'])
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
def not_found(error=False):
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
