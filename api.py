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

import flask
import flask.ext.httpauth

import redis

import cogs.auth
import cogs.structs


### Constants ###

_MSG_ROOT = "Welcome to the CU CS Online Grading System API\n"

_FILES_KEY = "files"
_REPORTERS_KEY = "reporters"
_ASSIGNMENTS_KEY = "assignments"
_TESTS_KEY = "tests"
_SUBMISSIONS_KEY = "submissions"
_RUNS_KEY = "runs"


### Global Setup ###

app = flask.Flask(__name__)
httpauth = flask.ext.httpauth.HTTPBasicAuth()
srv = cogs.structs.Server()
auth = cogs.auth.Auth()
workers = multiprocessing.Pool(10)

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

def create_stub_file(func_create, **kwargs):

    obj_lst = []
    files = flask.request.files
    for key in files:
        data = {}
        data['key'] = str(key)
        file_obj = files[key]
        obj = func_create(data, file_obj=file_obj, owner=flask.g.user, **kwargs)
        obj_lst.append(str(obj.uuid))
    return obj_lst

def update_stub_json(obj):

    data = flask.request.get_json(force=True)
    obj.set_dict(data)
    obj_dict = obj.get_dict()
    return obj_dict

def process_objects(func_list, func_create, key, create_stub=create_stub_json, **kwargs):

    # List Objects
    if flask.request.method == 'GET':

        obj_lst = list(func_list())

    # Create Object
    elif flask.request.method == 'POST':
        try:
            obj_lst = create_stub(func_create, **kwargs)
        except KeyError as e:
            return error_response(e, 400)

    # Bad Method
    else:
        raise Exception("Unhandled Method")

    # Return Object List
    out = {key: obj_lst}
    return flask.jsonify(out)

def process_object(func_get, obj_uuid, update_stub=update_stub_json):

    # Get Object
    obj = func_get(obj_uuid)

    # Get Object Data
    if flask.request.method == 'GET':
        obj_dict = obj.get_dict()

    # Update Object Data
    elif flask.request.method == 'PUT':
        try:
            obj_dict = update_stub(obj)
        except KeyError as e:
            return error_response(e, 400)

    # Delete Object
    elif flask.request.method == 'DELETE':
        obj_dict = obj.get_dict()
        obj.delete()

    # Bad Method
    else:
        raise Exception("Unhandled Method")

    # Return Object
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
        try:
            add_lst = sanitize_uuid_list(in_lst)
        except ValueError as e:
            return (None, error_response(e, 400))
        func_add(add_lst)
        out_lst = list(func_list())

    # Remove Objects
    elif flask.request.method == 'DELETE':
        in_obj = flask.request.get_json(force=True)
        in_lst = list(in_obj[key])
        try:
            rem_lst = sanitize_uuid_list(in_lst)
        except ValueError as e:
            return (None, error_response(e, 400))
        func_remove(rem_lst)
        out_lst = list(func_list())

    # Bad Method
    else:
        raise Exception("Unhandled Method")

    # Return Object List
    out_obj = {key: out_lst}
    return flask.jsonify(out_obj)


### Endpoints ###

## Root Endpoints ##

@app.route("/",
           methods=['GET'])
@httpauth.login_required
@auth.requires_auth_route()
def get_root():

    res = _MSG_ROOT
    return res

## Access Control Endpoints ##

# ToDo: All of Them...

## File Endpoints ##

@app.route("/files/", methods=['GET', 'POST'])
@httpauth.login_required
@auth.requires_auth_route()
def process_files():
    return process_objects(srv.list_files, srv.create_file, _FILES_KEY, create_stub=create_stub_file)

@app.route("/files/<obj_uuid>/", methods=['GET', 'DELETE'])
@httpauth.login_required
@get_owner(srv.get_file)
@auth.requires_auth_route()
def process_file(obj_uuid):
    return process_object(srv.get_file, obj_uuid, update_stub=None)

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
    return process_objects(sub.list_runs, sub.execute_run, _RUNS_KEY, workers=workers)

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
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

@app.errorhandler(cogs.structs.ObjectDNE)
def not_found(error=False):
    err = { 'status': 404,
            'message': "Not Found: {:s}".format(flask.request.url) }
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

@app.errorhandler(400)
def bad_request(error=False):
    err = { 'status': 400,
            'message': "Malformed request" }
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

@app.errorhandler(404)
def not_found(error=False):
    err = { 'status': 404,
            'message': "Not Found: {:s}".format(flask.request.url) }
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

@app.errorhandler(405)
def bad_method(error=False):
    err = { 'status': 405,
            'message': "Bad Method: {:s} {:s}".format(flask.request.method, flask.request.url) }
    res = flask.jsonify(err)
    res.status_code = err['status']
    return res

### Run Test Server ###

if __name__ == "__main__":
    app.run(debug=True)
