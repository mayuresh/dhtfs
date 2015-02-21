Tagging based filesystem, providing dynamic directory hierarchies based
on tags associated with files. 

This file contains the following topics:

- Quick usage guide
- Common problems and their solutions
- Philosophy behind this project
- Overall structure of the package
- Documentation 
- Licensing

Quick Usage Guide
===================

Install the dhtfs module following the instructions in INSTALL.
This is a layered filesystem. It is not created over a raw disk
but in a directory on some mounted filesystem.

The very basic usage is as follows. This will help you to get started.

$ cd $HOME

Create a directory which will be used to host the file system
$ mkdir newfs

Create the file system
$ mkfs.dhtfs --init-db newfs

Create a mount point
$ sudo mkdir /mnt/dhtfs

Mount the file system
$ mount.dhtfs /mnt/dhtfs -o root=newfs

Create a link to the mounted file system
$ ln -s /mnt/dhtfs dtest

Copy files to the new tagged file system
$ cp music/pink_floyd/Money.mp3 dtest
$ cp pics/sunset.jpg dtest

Add tags to the file
$ addTags dtest/Money.mp3 favorite music
$ addTags dtest/sunset.jpg favorite pics wallpaper

Look at the directory hierarchy generated
$ ls -lR dtest/

Go ahead .. add more files and tag them and browse thro them ...

Common Problems and their solutions
====================================

* Problem: 
-----------

Command fails with

fusermount: failed to open /dev/fuse: No such file or directory

* Solution: 

Insert the fuse module by running the modprobe command as root or sudo

$ sudo modprobe fuse

* Problem:
-----------

Mount command fails with

fusermount: user has no write access to mountpoint /mnt/dhtfs

* Solution:

Either change the permissions of the mountpoint to allow the
current user to access the mount point, by running the following
command. Replace USERNAME with the desired user

$ sudo chown USERNAME /mnt/dhtfs

OR run the mount comand as root.

* Problem
----------

Command fails with

ImportError: /usr/lib/libfuse.so.2: version `FUSE_2.5' not found (required by /usr/lib/python2.4/site-packages/fuseparts/_fusemodule.so)

OR

Required modules or libraries not setup properly

Solution:

This error occurs because the module is not able to find the required libraries.
Make sure you have installed everything as detialed in INSTALL.

Fuse adds its libraries to /usr/local/lib. Some systems may not use /usr/local/lib
as a standard path to search for libraries. You may have to add this path.

Modify LD_LIBRARY_PATH to include the path to fuse libraries.

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

Changing LD_LIBRARY_PATH is not a recommended solution. A better approach is to
edit the /etc/ld.so.conf and add /usr/local/lib to it. Run ldconfig to sync
the changes. 

Run the following commands as root

$ vi /etc/ld.so.conf

Add the line '/usr/local/lib'

Save the file

$ ldconfig




Philosophy behind this project
================================

Most file systems organize files in a directory hierarchy. A file is stored
in a particular directory. When it is needed to store a file, a decision has
to be made about the most suitable directory for the file.

This can be tough.

IMO, when presented with data, a human being generally associates a set of
attributes to data rather than looking at various attributes and selecting 
the best fit. i.e. On seeing a Lion, a human brain would attach attributes
like ferocious, wild, huge, carnivorous, etc. It would be tough, if ten
different attributes are given and the one most fitting attribute needs
to be assigned.

Similiarly, on observing some file, attributes like, music, favorite,
needs_backup, work, picture etc could spring up in mind. But while storing
the file it can only be stored in a single directory. Some workaround would
be done like storing a favourite picture in directory 'pics/favorite'.
The problem here is the hierarchy between 'pics' and 'favorite' is unchangable.
Browsing through all favorites from 'music', 'pics', 'poems' etc is quite cumbersome.

Tagging is a more intutive way of organizing data. All the attributes of a file
can be stored as tags to the file. Browsing through files by the tags associated
with them is easy.

The problem is that traditional file systems do not support a tagging structure.

This project aims at making the benefits of tagging available through a traditional
filesystem framework like VFS.

The aims of this project are as follows:

1. Integrate tagging with traditional filesystem (VFS)
2. The directory hierarchies should be dynamically generated depending on the tags
   associated with the files

Overall Structure
===================

The package 'dhtfs' consists of the following modules

GPStor - Provides persistent storage of python datatypes
Tagging - Provides primitive tagging operations
TagFile - Used to represent a file for tagging
TagDir - Extends Tagging and provides a wrapper over Tagging and implements filesystem specific operations
Dhtfs - Extends Fuse and provides filesystem operations for dhtfs

All the modules can be used individually and different systems could be developed using them.

The following scripts are provided:

mount.dhtfs - Used for mounting a dhtfs file system
mkfs.dhtfs - Used for creating a dhtfs file system
addTags - Used for adding tags to files in a mounted dhtfs file system
deltags - Used for deleting tags from files in a mounted dhtfs file system

Documentation
==============

The documentation of individual modules is contained in the directory 'docs'.
Help for the scripts can be got by running the scripts with '-h' option.

pydoc can be used to get documentation of modules.
Also the help command can be used from within the python interpretor to
get help about specific modules and functions.

Licensing
==========

The package is licenced under the 'New BSD License'.
The project is "Open source".

Individual files in this project can be copied and distributed under terms described in COPYING.
