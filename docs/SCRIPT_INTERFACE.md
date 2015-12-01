COG Grading Script Interface
================================

When using COG in grading script mode, it's important for the provided
script to adhere to the COG Grading Script Interface. Details of this
interface are discussed below.

Calling Convention
------------------

### Execution

COG attempts to execute the provided grading script as-is. Thus, the
provided grading script must be directly executable in a Linux
environment. In general, this means that:

 1. If the script is an interpreted program, it must begin with a
    shebang (i.e. `#!`) line indicating what interpreter should be
    called to execute it.
 2. If the script is a compiled program, it must be pre-compiled and
    the executable binary must be uploaded to COG.

Script authors need not worry about the permission set on the provided
script. These get lost and then reset by COG during the upload process
anyway, and COG will ensure that the provided script is marked as
executable.

### Arguments

COG will execute the provided grading script and pass it three arguments:

 1. The path to the directory containing the student submission (read-only).
 2. The path to the directory containing the grading script and any
    supporting files (read-only).
 3. The path to a scratch directory where you script has full access
    (read/write/create).

It is up to the grading script to process these arguments as necessary.

### Summery

Thus, the full COG call will look like:

 ```
 ./grading.script <submission directory path> <script directory path> <scratch directory path>
 ```

Output Convention
-----------------

### stdout and stderr

COG should output all errors, help messages, and other general output
on `stderr`. COG reserved `stdout` for the script to provide the final
student score. Thus, the only item printed to `stdout` should be a
single line parsable as either a positive integer or float value
representing the student's score for the test run.

All `stderr` output will be saved by COG and presented to the student
with their results. Thus, if you wish to communicate hints, test
notes, etc to the student, print them to `stderr`.

This also means that the grading script must police the use of
`stdout` or `stderr` by any sub-processes it happens to start: most
notably, the student submission itself. Most languages provide
mechanisms for capturing the `stderr` and `stdout` streams of a
sub-process. The grading script may either process these streams
directly, or pass them through to `stderr` for COG to pass to the
student. At no time should a sub-process be allowed to print directly
to `stdout`. Doing so will result in COG incorrectly trying to
interpret such output as the final student grade.

### Exit Value

A successful grading script execution should exit with the standard
zero-value. If a script exits with a non-zero value, COG will ignore
the grade the script may have output and instead report that an error
occurred executing the grading script. COG will provide the contents
of the script's `stderr` output to the screen if this occurs to allow
scripts to exit with non-zero values and report errors that can then
be read by either the student or script creator.

Environment
-----------

The environment in which COG executes the grading script depends on
the associated per-assignment 'env' module settings. In general,
however, grading scripts should not make assumptions about their
current working directory nor their ability to execute privileged
commands. If your script depends on running from a known working
directory, it is the script's responsibility to change to that
directory at the beginning of its execution. If your script requires
privileged commands (e.g. `sudo`), you will have to select an
environment that supports them.

COG scripts can assume that they will execute within at least a
`C.UTF8` locale. They will also have access to the standard `$PATH`
and `$PWD` environment variables. The `$HOME` environmental variable
will point to the scratch directory. Scripts may assume that they have
read and write access to `$HOME`.

COG scripts should assume that multiple executions may occur in
parallel. Thus, they should not depend on constant global directories
(e.g. `/tmp/grading_output`) for storing temporary files, etc. The
scratch directory path passed to the script when it is executed will
always point to a unique location for a given execution. Thus, it is
safe to write to or manipulate files in this directory without
effecting subsequent or concurrent runs.

Testing
-----------

A good way to test your script locally to make sure it follows the
above assumptions is as follows:

```
$ mkdir /tmp/test
$ mkdir /tmp/test/grader
$ mkdir /tmp/test/submission
$ mkdir /tmp/test/scratch
$ cp -r <grader code> /tmp/test/grader
$ cp -r <reference submission> /tmp/test/submission
$ chmod 777 /tmp/test/scratch
$ cd /tmp/test/scratch
$ sudo -u nobody -g nogroup /tmp/test/grader/<grader script> /tmp/test/submission/ /tmp/test/grader/ /tmp/test/scratch/
```

Note that this is not a perfect test - it doesn't do any real
sandboxing, nor does it add, remove, or update any environmental
variables (e.g. $HOME). It also shouldn't be assumed that the working
directory will be set to `/tmp/test/scratch`. But the above will at
least make sure you're using the cog calling convention and paths
correctly.
