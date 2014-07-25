#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import flask

app = flask.Flask(__name__)

@app.route("/", methods=['GET'])
def get_root():
    res = "Welcome to the CU CS Online Grading System"
    return res

# Add more routes/functions here

if __name__ == "__main__":
    app.run(debug=True)
