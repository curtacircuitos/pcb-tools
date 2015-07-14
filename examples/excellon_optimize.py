#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Example using pcb-tools with tsp-solver (github.com/dmishin/tsp-solver) to
# optimize tool paths in an Excellon file.
#
#
# Copyright 2015 Hamilton Kibbe <ham@hamiltonkib.be>
# Based on a script by https://github.com/koppi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import sys
import math
import gerber
from operator import sub
from gerber.excellon import DrillHit

try:
    from tsp_solver.greedy import solve_tsp
except ImportError:
    print('\n=================================================================\n'
          'This example requires tsp-solver be installed in order to run.\n\n'
          'tsp-solver can be downloaded from:\n'
          '    http://github.com/dmishin/tsp-solver.\n'
          '=================================================================')
    sys.exit(0)


if __name__ == '__main__':

    # Get file name to open
    if len(sys.argv) < 2:
        fname = 'gerbers/shld.drd'
    else:
        fname = sys.argv[1]

    # Read the excellon file
    f = gerber.read(fname)

    positions   = {}
    tools   = {}
    hit_counts = f.hit_count()
    oldpath = sum(f.path_length().values())

    #Get hit positions
    for hit in f.hits:
        tool_num = hit.tool.number
        if tool_num not in positions.keys():
            positions[tool_num]   = []
        positions[tool_num].append(hit.position)

    hits = []

    # Optimize tool path for each tool
    for tool, count in iter(hit_counts.items()):

        # Calculate distance matrix
        distance_matrix = [[math.hypot(*tuple(map(sub, 
                                                  positions[tool][i], 
                                                  positions[tool][j]))) 
                            for j in iter(range(count))] 
                            for i in iter(range(count))]

        # Calculate new path
        path = solve_tsp(distance_matrix, 50)

        # Create new hits list
        hits += [DrillHit(f.tools[tool], positions[tool][p]) for p in path]

    # Update the file
    f.hits = hits
    f.filename = f.filename + '.optimized'
    f.write()
    
    # Print drill report
    print(f.report())
    print('Original path length:  %1.4f' % oldpath)
    print('Optimized path length: %1.4f' % sum(f.path_length().values()))

