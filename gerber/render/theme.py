#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2014 Paulo Henrique Silva <ph.silva@gmail.com>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


COLORS = {
    'black': (0.0, 0.0, 0.0),
    'white': (1.0, 1.0, 1.0),
    'fr-4': (0.702, 0.655, 0.192),
    'green soldermask': (0.0, 0.612, 0.396),
    'blue soldermask': (0.059, 0.478, 0.651),
    'red soldermask': (0.968, 0.169, 0.165),
    'black soldermask': (0.298, 0.275, 0.282),
    'enig copper': (0.780, 0.588, 0.286),
    'hasl copper': (0.871, 0.851, 0.839)
}


class RenderSettings(object):
    def __init__(self, color, alpha=1.0, invert=False):
        self.color = color
        self.alpha = alpha
        self.invert = False


class Theme(object):
    def __init__(self, **kwargs):
        self.background = kwargs.get('background', RenderSettings(COLORS['black'], 0.0))
        self.topsilk = kwargs.get('topsilk', RenderSettings(COLORS['white']))
        self.topsilk = kwargs.get('bottomsilk', RenderSettings(COLORS['white']))
        self.topmask = kwargs.get('topmask', RenderSettings(COLORS['green soldermask'], 0.8, True))
        self.topmask = kwargs.get('topmask', RenderSettings(COLORS['green soldermask'], 0.8, True))
        self.top = kwargs.get('top', RenderSettings(COLORS['hasl copper']))
        self.bottom = kwargs.get('top', RenderSettings(COLORS['hasl copper']))
        self.drill = kwargs.get('drill', self.background)


