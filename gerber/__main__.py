#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2014 Paulo Henrique Silva <ph.silva@gmail.com>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

if __name__ == '__main__':
    from gerber.common import read
    from gerber.render import GerberCairoContext
    import sys

    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python -m gerber <filename> <filename>...\n")
        sys.exit(1)

    ctx = GerberCairoContext()
    ctx.alpha = 0.95
    for filename in sys.argv[1:]:
        print("parsing %s" % filename)
        if 'GTO' in filename or 'GBO' in filename:
            ctx.color = (1, 1, 1)
            ctx.alpha = 0.8
        elif 'GTS' in filename or 'GBS' in filename:
            ctx.color = (0.2, 0.2, 0.75)
            ctx.alpha = 0.8
        gerberfile = read(filename)
        gerberfile.render(ctx)

    print('Saving image to test.svg')
    ctx.dump('test.svg')
