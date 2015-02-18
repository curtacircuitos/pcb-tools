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


def read(filename):
    """ Read a gerber or excellon file and return a representative object.

    Parameters
    ----------
    filename : string
        Filename of the file to read.

    Returns
    -------
    file : CncFile subclass
        CncFile object representing the file, either GerberFile or
        ExcellonFile. Returns None if file is not an Excellon or Gerber file.
    """
    from . import rs274x
    from . import excellon
    from .utils import detect_file_format
    fmt = detect_file_format(filename)
    if fmt == 'rs274x':
        return rs274x.read(filename)
    elif fmt == 'excellon':
        return excellon.read(filename)
    else:
        raise TypeError('Unable to detect file format')

