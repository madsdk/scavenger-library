#!/bin/sh

SCRPC="git://github.com/madsdk/python-single-connection-RPC.git"
DATASTORE="git://github.com/madsdk/python-remote-data-store.git"
PRESENCE="git://github.com/madsdk/presence.git"
SCAVENGER="git://github.com/madsdk/scavenger-library.git"
PYTHON=$1
CWD=`pwd`

# Check command line arguments.
if [ "$1" = "" ]; then 
	echo "Usage: $0 /path/to/python/interpreter";
	exit 1
fi

# Check for dependencies (git).
if [ "`which git`" = "" ]; then
	echo "This build script depends upon git. Please install git.";
	exit 1
fi

# Fetch and install dependencies.
mkdir /tmp/scavenger-install
cd /tmp/scavenger-install

# SCRPC
git clone $SCRPC;		
cd python-single-connection-RPC/build;
./build.sh 1.0
cd scrpc-1.0
$PYTHON setup.py install
cd ../../..

# data store
git clone $DATASTORE;		
cd python-remote-data-store/build;
./build.sh 1.0
cd datastore-1.0
$PYTHON setup.py install
cd ../../..

# presence
git clone $PRESENCE;		
cd presence/builds/python_client_lib;
./build.sh 1.0
cd presence_client_lib-1.0
$PYTHON setup.py install
cd ../../../..

# Scavenger lib
git clone $SCAVENGER;		
cd scavenger-library/build;
./build.sh 1.0
cd scavenger-1.0
$PYTHON setup.py install
cd ../../..


cd $PWD
rm -rf /tmp/scavenger-install


exit 0
