#! /usr/bin/env python
# -*- coding: utf-8 -*-

# copyright 2014 Hamilton Kibbe <ham@hamiltonkib.be>
# Modified from parser.py by Paulo Henrique Silva <ph.silva@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math
import re
from .cam import FileSettings

# Net Name Variables
_NNAME = re.compile(r'^NNAME\d+$')

# Board Edge Coordinates
_COORD = re.compile(r'X?(?P<x>[\d\s]*)?Y?(?P<y>[\d\s]*)?')


def read(filename):
    """ Read data from filename and return an IPC_D_356
    Parameters
        ----------
    filename : string
        Filename of file to parse

    Returns
    -------
    file : :class:`gerber.ipc356.IPC_D_356`
        An IPC_D_356 object created from the specified file.

    """
    # File object should use settings from source file by default.
    return IPC_D_356.from_file(filename)


class IPC_D_356(object):

    @classmethod
    def from_file(self, filename):
        p = IPC_D_356_Parser()
        return p.parse(filename)


    def __init__(self, statements, settings):
        self.statements = statements
        self.units = settings.units
        self.angle_units = settings.angle_units

    @property
    def settings(self):
        return FileSettings(units=self.units, angle_units=self.angle_units)

    @property
    def comments(self):
        return [record for record in self.statements
                if isinstance(record, IPC356_Comment)]

    @property
    def parameters(self):
        return [record for record in self.statements
                if isinstance(record, IPC356_Parameter)]

    @property
    def test_records(self):
        return [record for record in self.statements
                if isinstance(record, IPC356_TestRecord)]

    @property
    def nets(self):
        return list(set([rec.net_name for rec in self.test_records
                         if rec.net_name is not None]))

    @property
    def components(self):
        return list(set([rec.id for rec in self.test_records
                         if rec.id is not None and rec.id != 'VIA']))

    @property
    def vias(self):
        return [rec.id for rec in self.test_records if rec.id == 'VIA']

    @property
    def board_outline(self):
        outline = [stmt for stmt in self.statements if isinstance(stmt, IPC356_BoardEdge)]
        if len(outline):
            return outline[0].points
        else:
            return None

class IPC_D_356_Parser(object):
    # TODO: Allow multi-line statements (e.g. Altium board edge)
    def __init__(self):
        self.units = 'inch'
        self.angle_units = 'degrees'
        self.statements = []
        self.nnames = {}

    @property
    def settings(self):
        return FileSettings(units=self.units, angle_units=self.angle_units)

    def parse(self, filename):
        with open(filename, 'r') as f:
            for line in f:

                if line[0] == 'C':
                    # Comment
                    self.statements.append(IPC356_Comment.from_line(line))

                elif line[0] == 'P':
                    # Parameter
                    p = IPC356_Parameter.from_line(line)
                    if p.parameter == 'UNITS':
                        if p.value in ('CUST', 'CUST 0'):
                            self.units = 'inch'
                            self.angle_units = 'degrees'
                        elif p.value == 'CUST 1':
                            self.units = 'metric'
                            self.angle_units = 'degrees'
                        elif p.value == 'CUST 2':
                            self.units = 'inch'
                            self.angle_units = 'radians'
                    self.statements.append(p)
                    if _NNAME.match(p.parameter):
                        # Add to list of net name variables
                        self.nnames[p.parameter] = p.value

                elif line[0] == '3' and line[2] == '7':
                    # Test Record
                    record = IPC356_TestRecord.from_line(line, self.settings)

                    # Substitute net name variables
                    net = record.net_name
                    if (_NNAME.match(net) and net in self.nnames.keys()):
                        record.net_name = self.nnames[record.net_name]
                    self.statements.append(record)

                elif line[0:3] == '389':
                    # Altium Board Edge Info
                    self.statements.append(IPC356_BoardEdge.from_line(line, self.settings))

                elif line[0] == '9':
                    self.multiline = False
                    self.statements.append(IPC356_EndOfFile())

        return IPC_D_356(self.statements, self.settings)


class IPC356_Comment(object):
    @classmethod
    def from_line(cls, line):
        if line[0] != 'C':
            raise ValueError('Not a valid comment statment')
        comment = line[2:].strip()
        return cls(comment)

    def __init__(self, comment):
        self.comment = comment

    def __repr__(self):
        return '<IPC-D-356 Comment: %s>' % self.comment


class IPC356_Parameter(object):
    @classmethod
    def from_line(cls, line):
        if line[0] != 'P':
            raise ValueError('Not a valid parameter statment')
        splitline = line[2:].split()
        parameter = splitline[0].strip()
        value = ' '.join(splitline[1:]).strip()
        return cls(parameter, value)

    def __init__(self, parameter, value):
        self.parameter = parameter
        self.value = value

    def __repr__(self):
        return '<IPC-D-356 Parameter: %s=%s>' % (self.parameter, self.value)


class IPC356_TestRecord(object):
    @classmethod
    def from_line(cls, line, settings):
        units = settings.units
        angle = settings.angle_units
        feature_types = {'1':'through-hole', '2': 'smt',
                         '3':'tooling-feature', '4':'tooling-hole'}
        access = ['both', 'top', 'layer2', 'layer3', 'layer4', 'layer5',
                  'layer6', 'layer7', 'bottom']
        record = {}
        line = line.strip()
        if line[0] != '3':
            raise ValueError('Not a valid test record statment')
        record['feature_type'] = feature_types[line[1]]

        end = len(line) - 1 if len(line) < 18 else 17
        record['net_name'] = line[3:end].strip()

        end = len(line) - 1 if len(line) < 27 else 26
        record['id'] = line[20:end].strip()

        end = len(line) - 1 if len(line) < 32 else 31
        record['pin'] = (line[27:end].strip() if line[27:end].strip() != ''
                         else None)

        record['location'] = 'middle' if line[31] == 'M' else 'end'
        if line[32] == 'D':
            end = len(line) - 1 if len(line) < 38 else 37
            dia = int(line[33:end].strip())
            record['hole_diameter'] = (dia * 0.0001 if units == 'inch'
                                       else dia * 0.001)
        if len(line) >= 38:
            record['plated'] = (line[37] == 'P')

        if len(line) >= 40:
            end = len(line) - 1 if len(line) < 42 else 41
            record['access'] = access[int(line[39:end])]

        if len(line) >= 43:
            end = len(line) - 1 if len(line) < 50 else 49
            coord = int(line[42:49].strip())
            record['x_coord'] = (coord *  0.0001 if units == 'inch'
                                 else coord * 0.001)

        if len(line) >= 51:
            end = len(line) - 1 if len(line) < 58 else 57
            coord = int(line[50:57].strip())
            record['y_coord'] = (coord *  0.0001 if units == 'inch'
            else coord * 0.001)

        if len(line) >= 59:
            end = len(line) - 1 if len(line) < 63 else 62
            dim = line[58:62].strip()
            if dim != '':
                record['rect_x'] = (int(dim) * 0.0001 if units == 'inch'
                                else int(dim) * 0.001)

        if len(line) >= 64:
            end = len(line) - 1 if len(line) < 68 else 67
            dim = line[63:67].strip()
            if dim != '':
                record['rect_y'] = (int(dim) * 0.0001 if units == 'inch'
                                    else int(dim) * 0.001)

        if len(line) >= 69:
            end = len(line) - 1 if len(line) < 72 else 71
            rot = line[68:71].strip()
            if rot != '':
                record['rect_rotation'] = (int(rot) if angle == 'degrees'
                                           else math.degrees(rot))

        if len(line) >= 74:
            end = len(line) - 1 if len(line) < 75 else 74
            record['soldermask_info'] = line[73:74].strip()

        if len(line) >= 76:
            end = len(line) - 1 if len(line < 80) else 79
            record['optional_info'] = line[75:end]

        return cls(**record)

    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def __repr__(self):
        return '<IPC-D-356 Test Record: Net: %s Type: %s>' % (self.net_name,
                                                            self.feature_type)

class IPC356_BoardEdge(object):

    @classmethod
    def from_line(cls, line, settings):
        scale = 0.0001 if settings.units == 'inch' else 0.001
        points = []
        x = 0
        y = 0
        coord_strings = line.strip().split()[1:]
        for coord in coord_strings:
            coord_dict = _COORD.match(coord).groupdict()
            x = int(coord_dict['x']) if coord_dict['x'] is not '' else x
            y = int(coord_dict['y']) if coord_dict['y'] is not '' else y
            points.append((x * scale, y * scale))
        return cls(points)

    def __init__(self, points):
        self.points = points

    def __repr__(self):
        return '<IPC-D-356 Board Edge Definition>'



class IPC356_EndOfFile(object):
    def __init__(self):
        pass

    def to_netlist(self):
        return '999'

    def __repr__(self):
        return '<IPC-D-356 EOF>'
