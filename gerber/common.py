#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2014 Hamilton Kibbe <ham@hamiltonkib.be>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from . import rs274x
from . import excellon
from . import ipc356
from .exceptions import ParseError
from .utils import detect_file_format


def read(filename):
    """ Read a gerber or excellon file and return a representative object.

    Parameters
    ----------
    filename : string
        Filename of the file to read.

    Returns
    -------
    file : CncFile subclass
        CncFile object representing the file, either GerberFile, ExcellonFile,
        or IPCNetlist. Returns None if file is not of the proper type.
    """
    with open(filename, 'rU') as f:
        data = f.read()
    return loads(data, filename)


def loads(data, filename=None):
    """ Read gerber or excellon file contents from a string and return a
    representative object.

    Parameters
    ----------
    data : string
        Source file contents as a string.

    filename : string, optional
        String containing the filename of the data source.

    Returns
    -------
    file : CncFile subclass
        CncFile object representing the data, either GerberFile, ExcellonFile,
        or IPCNetlist. Returns None if data is not of the proper type.
    """

    fmt = detect_file_format(data)
    if fmt == 'rs274x':
        return rs274x.loads(data, filename=filename)
    elif fmt == 'excellon':
        return excellon.loads(data, filename=filename)
    elif fmt == 'ipc_d_356':
        return ipc356.loads(data, filename=filename)
    else:
        raise ParseError('Unable to detect file format')
