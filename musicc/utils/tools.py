# MUSICC - Multi User Scenario Catalogue for Connected and Autonomous Vehicles
# Copyright (C)2020 Connected Places Catapult
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact: musicc-support@cp.catapult.org.uk
#          https://cp.catapult.org.uk/case-studies/musicc/'
#
## @package tools
#  This module contains utilities for general use in the MUSICC project<br>
#  An example is that of a temporary change to a working directory for a<br>
#  small section of code.

import os
import shutil
from contextlib import contextmanager
from django.http import HttpResponse, Http404, FileResponse

import sys
import time
import datetime
import inspect

import hashlib


## Returns nothing
#  @param stuff one (or none) or more arguments that you want printing
#  @details Example demonstration of use:
#
#  The function is to be used for issuing warnings on stdout and to provide useful
#  context of where #  it was called from (filename and lineno).
#  @details Example demonstration of use:
#
#  @code
#      warning("Problem with element", index, "time:", time.localtime())
#  @endcode
#
def warning(*objs):
    print(
        "WARNING: ",
        os.path.basename(inspect.currentframe().f_back.f_globals["__file__"]),
        inspect.currentframe().f_back.f_lineno,
        *objs,
        sep=" ",
        flush=True
    )  # note use of line number information from the previous stackframe


## Returns nothing
#  @param verbosity boolean flag. If True then print.
#  @param objs one (or none) or more arguments that you want printing
#  @details Example demonstration of use:
#
#  The function is to be used for providing information (filename and lineno) on stdout
#  as an alternative to using a debugger or logging. The boolean flag allows dynamic toggling
#  so as to facilitate the selective use of trace/debug information i.e. not printing out swathes
#  of information where it is not required.
#  @details Example demonstration of use:
#
#  @code
#      module_flag = True # Probably set at top of module
#      .....
#      .....
#      information(module_flag, "Problem with element", index, "time:", time.asctime(time.localtime())
#  @endcode
#
def information(verbosity, *objs):
    if verbosity:
        print(
            "Information: ",
            os.path.basename(inspect.currentframe().f_back.f_globals["__file__"]),
            inspect.currentframe().f_back.f_lineno,
            *objs,
            sep=" ",
            flush=True
        )  # note use of line number information from the previous stackframe


## Returns generator value of found keys
# @param key_to_find Key to find
# @param dictionary Dictionary to search
#
# Function cycles through a dictionary finding a particular value
def find_keys_in_dictionary(key_to_find, dictionary):
    for key, value in dictionary.items():
        if key == key_to_find:
            yield value
        elif isinstance(value, dict):
            for result in find_keys_in_dictionary(key_to_find, value):
                yield result


## Returns nothing
#  @param directory The directory to use as a temporary working directory
#  @details Example demonstration of use:
#
#  The function is to be used where you want to change the working
#  directory context for a shot period and to recover the original context.
#  Behind the scenes the contextlib https://docs.python.org/3/library/contextlib.html
#  is used.
#
#  @code
#      # open and read xml file
#       with working_directory(dirname_xml):
#           with open(basename_xml, "r") as xml_file:
#               xml_to_check = xml_file.read()
#  @endcode


@contextmanager
def working_directory(directory):
    owd = os.getcwd()
    try:
        os.chdir(directory)
        yield directory
    finally:
        os.chdir(owd)

## Get an md5 hash of a file
#  @param file The file content
#  @return The hash in hex
def get_file_hash(file):
    file_hash = hashlib.md5(file)
    return file_hash.hexdigest()

## Get an md5 hash of a large chunked zip file or django file object
#  @param uploaded_zip_file The file
#  @return The hash in hex
def get_uploaded_zip_file_hash(uploaded_zip_file):
    hash_md5 = hashlib.md5()

    if hasattr(uploaded_zip_file, "read"):
        for chunk in uploaded_zip_file.chunks():
            hash_md5.update(chunk)
    elif hasattr(uploaded_zip_file, "file"):
         with open(uploaded_zip_file.file, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
    
    return hash_md5.hexdigest()

## Create a Django FileResponse for a given opened file
#  @param file An open file
#  @param target_file_name The name which this file should have when downloaded
#  @return A FileResponse or 404 error if the file doesn't exist
def create_zip_file_stream_response(file, target_file_name):
    try:
        response = FileResponse(file, as_attachment=True, filename=target_file_name)

    except FileNotFoundError:
        raise Http404("File does not exist")

    return response

## Delete a folder if it exists
#  @param folder_name The folder to delete
def delete_folder_if_exists(folder_name):
    if os.path.isdir(folder_name):
        shutil.rmtree(folder_name)

def unique(sequence):
    seen = set()
    return [x for x in sequence if not (x in seen or seen.add(x))]

## Order query set accounting for musicc, openscenario or opendrive ID which are not specified in the metadata
# @param query_set Query set to sort
# @param order_direction Direction in which to order, either 'asc' or 'desc'
# @param order_column Column to order
# @return Ordered query set
def order_query_set(query_set, order_direction, order_column):
    if 'metadata__MUSICC_ID' in order_column :
        order_column = 'friendly_id'
    elif 'metadata__OpenScenario_ID' in order_column :
        order_column = 'scenario__friendly_id'
    elif 'metadata__OpenDrive_ID' in order_column :
        order_column = 'open_drive__friendly_id'
    query_set = query_set.order_by(order_direction+order_column)
    return(query_set)
