#!/bin/sh

SRCDIR=../src/

# Check for version number
if [ "$1" = "" ]; then
	echo "Usage: build.sh version_number";
	exit 1
else
	VERSION="$1"
fi
BUILDDIR=scavenger-$VERSION

# Create the $BUILDDIR dir
if [ -d $BUILDDIR ]; then 
	rm -rf $BUILDDIR;
fi
mkdir -p $BUILDDIR/scavenger/schedule

# Copy python files into the $BUILDDIR dir.
cp $SRCDIR/scavenger/*.py $BUILDDIR/scavenger
cp $SRCDIR/scavenger/schedule/*.py $BUILDDIR/scavenger/schedule/
cp setup.py $BUILDDIR/
sed -i "" s/VERSION/$VERSION/ $BUILDDIR/setup.py

tar cfz $BUILDDIR.tar.gz $BUILDDIR

exit 0
