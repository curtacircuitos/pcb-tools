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
from .cam import CamFile, FileSettings
from .primitives import TestRecord

# Net Name Variables
_NNAME = re.compile(r'^NNAME\d+$')

# Board Edge Coordinates
_COORD = re.compile(r'X?(?P<x>[\d\s]*)?Y?(?P<y>[\d\s]*)?')

_SM_FIELD = {
    '0': 'none',
    '1': 'primary side',
    '2': 'secondary side',
    '3': 'both'}


def read(filename):
    """ Read data from filename and return an IPCNetlist
    Parameters
        ----------
    filename : string
        Filename of file to parse

    Returns
    -------
    file : :class:`gerber.ipc356.IPCNetlist`
        An IPCNetlist object created from the specified file.

    """
    # File object should use settings from source file by default.
    return IPCNetlist.from_file(filename)


def loads(data, filename=None):
    """ Generate an IPCNetlist object from IPC-D-356 data in memory

    Parameters
    ----------
    data : string
        string containing netlist file contents

    filename : string, optional
        string containing the filename of the data source

    Returns
    -------
    file : :class:`gerber.ipc356.IPCNetlist`
        An IPCNetlist created from the specified file.
    """
    return IPCNetlistParser().parse_raw(data, filename)


class IPCNetlist(CamFile):

    @classmethod
    def from_file(cls, filename):
        parser = IPCNetlistParser()
        return parser.parse(filename)

    def __init__(self, statements, settings, primitives=None, filename=None):
        self.statements = statements
        self.units = settings.units
        self.angle_units = settings.angle_units
        self.primitives = [TestRecord((rec.x_coord, rec.y_coord), rec.net_name,
                                      rec.access) for rec in self.test_records]
        self.filename = filename

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
        nets = []
        for net in list(set([rec.net_name for rec in self.test_records
                             if rec.net_name is not None])):
            adjacent_nets = set()
            for record in self.adjacency_records:
                if record.net == net:
                    adjacent_nets = adjacent_nets.update(record.adjacent_nets)
                elif net in record.adjacent_nets:
                    adjacent_nets.add(record.net)
            nets.append(IPC356_Net(net, adjacent_nets))
        return nets

    @property
    def components(self):
        return list(set([rec.id for rec in self.test_records
                         if rec.id is not None and rec.id != 'VIA']))

    @property
    def vias(self):
        return [rec.id for rec in self.test_records if rec.id == 'VIA']

    @property
    def outlines(self):
        return [stmt for stmt in self.statements
                if isinstance(stmt, IPC356_Outline)]

    @property
    def adjacency_records(self):
        return [record for record in self.statements
                if isinstance(record, IPC356_Adjacency)]

    def render(self, ctx, layer='both', filename=None):
        for p in self.primitives:
            if layer == 'both' and p.layer in ('top', 'bottom', 'both'):
                ctx.render(p)
            elif layer == 'top' and p.layer in ('top', 'both'):
                ctx.render(p)
            elif layer == 'bottom' and p.layer in ('bottom', 'both'):
                ctx.render(p)
        if filename is not None:
            ctx.dump(filename)


class IPCNetlistParser(object):
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
        with open(filename, 'rU') as f:
            data = f.read()
        return self.parse_raw(data, filename)

    def parse_raw(self, data, filename=None):
        oldline = ''
        for line in data.splitlines():
            # Check for existing multiline data...
                if oldline != '':
                    if len(line) and line[0] == '0':
                        oldline = oldline.rstrip('\r\n') + line[3:].rstrip()
                    else:
                        self._parse_line(oldline)
                        oldline = line
                else:
                    oldline = line
        self._parse_line(oldline)

        return IPCNetlist(self.statements, self.settings, filename=filename)

    def _parse_line(self, line):
        if not len(line):
            return
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

        elif line[0] == '9':
            self.statements.append(IPC356_EndOfFile())

        elif line[0:3] in ('317', '327', '367'):
            # Test Record
            record = IPC356_TestRecord.from_line(line, self.settings)

            # Substitute net name variables
            net = record.net_name
            if (_NNAME.match(net) and net in self.nnames.keys()):
                record.net_name = self.nnames[record.net_name]
            self.statements.append(record)

        elif line[0:3] == '378':
            # Conductor
            self.statements.append(
                IPC356_Conductor.from_line(
                    line, self.settings))

        elif line[0:3] == '379':
            # Net Adjacency
            self.statements.append(IPC356_Adjacency.from_line(line))

        elif line[0:3] == '389':
            # Outline
            self.statements.append(
                IPC356_Outline.from_line(
                    line, self.settings))


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
        offset = 0
        units = settings.units
        angle = settings.angle_units
        feature_types = {'1': 'through-hole', '2': 'smt',
                         '3': 'tooling-feature', '4': 'tooling-hole',
                         '6': 'non-plated-tooling-hole'}
        access = ['both', 'top', 'layer2', 'layer3', 'layer4', 'layer5',
                  'layer6', 'layer7', 'bottom']
        record = {}
        line = line.strip()
        if line[0] != '3':
            raise ValueError('Not a valid test record statment')
        record['feature_type'] = feature_types[line[1]]

        end = len(line) - 1 if len(line) < 18 else 17
        record['net_name'] = line[3:end].strip()

        if len(line) >= 27 and line[26] != '-':
            offset = line[26:].find('-')
            offset = 0 if offset == -1 else offset
        end = len(line) - 1 if len(line) < (27 + offset) else (26 + offset)
        record['id'] = line[20:end].strip()

        end = len(line) - 1 if len(line) < (32 + offset) else (31 + offset)
        record['pin'] = (line[27 + offset:end].strip() if line[27 + offset:end].strip() != ''
                         else None)

        record['location'] = 'middle' if line[31 + offset] == 'M' else 'end'
        if line[32 + offset] == 'D':
            end = len(line) - 1 if len(line) < (38 + offset) else (37 + offset)
            dia = int(line[33 + offset:end].strip())
            record['hole_diameter'] = (dia * 0.0001 if units == 'inch'
                                       else dia * 0.001)
        if len(line) >= (38 + offset):
            record['plated'] = (line[37 + offset] == 'P')

        if len(line) >= (40 + offset):
            end = len(line) - 1 if len(line) < (42 + offset) else (41 + offset)
            record['access'] = access[int(line[39 + offset:end])]

        if len(line) >= (43 + offset):
            end = len(line) - 1 if len(line) < (50 + offset) else (49 + offset)
            coord = int(line[42 + offset:end].strip())
            record['x_coord'] = (coord * 0.0001 if units == 'inch'
                                 else coord * 0.001)

        if len(line) >= (51 + offset):
            end = len(line) - 1 if len(line) < (58 + offset) else (57 + offset)
            coord = int(line[50 + offset:end].strip())
            record['y_coord'] = (coord * 0.0001 if units == 'inch'
                                 else coord * 0.001)

        if len(line) >= (59 + offset):
            end = len(line) - 1 if len(line) < (63 + offset) else (62 + offset)
            dim = line[58 + offset:end].strip()
            if dim != '':
                record['rect_x'] = (int(dim) * 0.0001 if units == 'inch'
                                    else int(dim) * 0.001)

        if len(line) >= (64 + offset):
            end = len(line) - 1 if len(line) < (68 + offset) else (67 + offset)
            dim = line[63 + offset:end].strip()
            if dim != '':
                record['rect_y'] = (int(dim) * 0.0001 if units == 'inch'
                                    else int(dim) * 0.001)

        if len(line) >= (69 + offset):
            end = len(line) - 1 if len(line) < (72 + offset) else (71 + offset)
            rot = line[68 + offset:end].strip()
            if rot != '':
                record['rect_rotation'] = (int(rot) if angle == 'degrees'
                                           else math.degrees(rot))

        if len(line) >= (74 + offset):
            end = 74 + offset
            sm_info = line[73 + offset:end].strip()
            record['soldermask_info'] = _SM_FIELD.get(sm_info)

        if len(line) >= (76 + offset):
            end = len(line) - 1 if len(line) < (80 + offset) else 79 + offset
            record['optional_info'] = line[75 + offset:end]

        return cls(**record)

    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def __repr__(self):
        return '<IPC-D-356 %s Test Record: %s>' % (self.net_name,
                                                   self.feature_type)


class IPC356_Outline(object):

    @classmethod
    def from_line(cls, line, settings):
        type = line[3:17].strip()
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
        return cls(type, points)

    def __init__(self, type, points):
        self.type = type
        self.points = points

    def __repr__(self):
        return '<IPC-D-356 %s Outline Definition>' % self.type


class IPC356_Conductor(object):

    @classmethod
    def from_line(cls, line, settings):
        if line[0:3] != '378':
            raise ValueError('Not a valid IPC-D-356 Conductor statement')

        scale = 0.0001 if settings.units == 'inch' else 0.001
        net_name = line[3:17].strip()
        layer = int(line[19:21])

        # Parse out aperture definiting
        raw_aperture = line[22:].split()[0]
        aperture_dict = _COORD.match(raw_aperture).groupdict()
        x = 0
        y = 0
        x = int(aperture_dict['x']) * \
            scale if aperture_dict['x'] is not '' else None
        y = int(aperture_dict['y']) * \
            scale if aperture_dict['y'] is not '' else None
        aperture = (x, y)

        # Parse out conductor shapes
        shapes = []
        coord_list = ' '.join(line[22:].split()[1:])
        raw_shapes = coord_list.split('*')
        for rshape in raw_shapes:
            x = 0
            y = 0
            shape = []
            coords = rshape.split()
            for coord in coords:
                coord_dict = _COORD.match(coord).groupdict()
                x = int(coord_dict['x']) if coord_dict['x'] is not '' else x
                y = int(coord_dict['y']) if coord_dict['y'] is not '' else y
                shape.append((x * scale, y * scale))
            shapes.append(tuple(shape))
        return cls(net_name, layer, aperture, tuple(shapes))

    def __init__(self, net_name, layer, aperture, shapes):
        self.net_name = net_name
        self.layer = layer
        self.aperture = aperture
        self.shapes = shapes

    def __repr__(self):
        return '<IPC-D-356 %s Conductor Record>' % self.net_name


class IPC356_Adjacency(object):

    @classmethod
    def from_line(cls, line):
        if line[0:3] != '379':
            raise ValueError('Not a valid IPC-D-356 Conductor statement')
        nets = line[3:].strip().split()

        return cls(nets[0], nets[1:])

    def __init__(self, net, adjacent_nets):
        self.net = net
        self.adjacent_nets = adjacent_nets

    def __repr__(self):
        return '<IPC-D-356 %s Adjacency Record>' % self.net


class IPC356_EndOfFile(object):

    def __init__(self):
        pass

    def to_netlist(self):
        return '999'

    def __repr__(self):
        return '<IPC-D-356 EOF>'


class IPC356_Net(object):

    def __init__(self, name, adjacent_nets):
        self.name = name
        self.adjacent_nets = set(
            adjacent_nets) if adjacent_nets is not None else set()

    def __repr__(self):
        return '<IPC-D-356 Net %s>' % self.name
