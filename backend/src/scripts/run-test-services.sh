#!/usr/bin/env bash

# Start a cockroachdb instance that can be used in conjunction with tests.
# The connection details will be written to a file in tmp.
# The appropriate environment variable / file path will be printed out to user
# so they can copy/paste it and set env before running the tests.

# This is a developer speed opimization, allowing those fixtures to bypass starting and managing
# those services themselves.

sql_port=54368
http_port=54369

crdb_user="root"
crdb_password=""

if [ -z "$TMPDIR" ]; then
        # WSL is missing $TMPDIR, maybe other platforms too?
        TMPDIR=/tmp
fi

if [ ! -d "$TMPDIR" ]; then
        echo "\$TMPDIR '$TMPDIR' does not exist / is not a directory."
        echo "Sorry, I can't tell where to put tmp files. Please set \$TMPDIR to a writeable dir."
        exit 1
fi


cat > "$TMPDIR"/crdb.json << EOF
{
        "hostname": "localhost",
        "port": $sql_port,
        "username": "$crdb_user",
        "password": "$crdb_password",
        "dbname": "defaultdb"
}
EOF

echo "Before running first test pass, set these:"
echo ""
echo "TEST_CRDB_DETAILS=\"$TMPDIR/crdb.json\"; export TEST_CRDB_DETAILS"
echo ""
echo "If you change any schema elements between test runs, safest to just control-C this"
echo "and re-run. (You won't need to reset the environment variables -- just functions of \$TMPDIR.)"
echo ""
echo "Now running insecure CRDB at SQL port $sql_port and http port $http_port."
echo "To connect and inspect post-test data, run 'cockroach sql --host=localhost:$sql_port --insecure'"
echo ""
echo "(control-c to kill)"

(cd "$TMPDIR" || exit 1 && cockroach start-single-node --insecure --listen-addr localhost:$sql_port --http-addr localhost:$http_port --store=type=mem,size=641mib >& /dev/null)
