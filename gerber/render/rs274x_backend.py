"""Renders an in-memory Gerber file to statements which can be written to a string
"""
from copy import deepcopy

try:
    from cStringIO import StringIO
except(ImportError):
    from io import StringIO

from .render import GerberContext
from ..am_statements import *
from ..gerber_statements import *
from ..primitives import AMGroup, Arc, Circle, Line, Obround, Outline, Polygon, Rectangle


class AMGroupContext(object):
    '''A special renderer to generate aperature macros from an AMGroup'''

    def __init__(self):
        self.statements = []

    def render(self, amgroup, name):

        if amgroup.stmt:
            # We know the statement it was generated from, so use that to create the AMParamStmt
            # It will give a much better result

            stmt = deepcopy(amgroup.stmt)
            stmt.name = name

            return stmt

        else:
            # Clone ourselves, then offset by the psotion so that
            # our render doesn't have to consider offset. Just makes things simpler
            nooffset_group = deepcopy(amgroup)
            nooffset_group.position = (0, 0)

            # Now draw the shapes
            for primitive in nooffset_group.primitives:
                if isinstance(primitive, Outline):
                    self._render_outline(primitive)
                elif isinstance(primitive, Circle):
                    self._render_circle(primitive)
                elif isinstance(primitive, Rectangle):
                    self._render_rectangle(primitive)
                elif isinstance(primitive, Line):
                    self._render_line(primitive)
                elif isinstance(primitive, Polygon):
                    self._render_polygon(primitive)
                else:
                    raise ValueError('amgroup')

            statement = AMParamStmt('AM', name, self._statements_to_string())
            return statement

    def _statements_to_string(self):
        macro = ''

        for statement in self.statements:
            macro += statement.to_gerber()

        return macro

    def _render_circle(self, circle):
        self.statements.append(AMCirclePrimitive.from_primitive(circle))

    def _render_rectangle(self, rectangle):
        self.statements.append(AMCenterLinePrimitive.from_primitive(rectangle))

    def _render_line(self, line):
        self.statements.append(AMVectorLinePrimitive.from_primitive(line))

    def _render_outline(self, outline):
        self.statements.append(AMOutlinePrimitive.from_primitive(outline))

    def _render_polygon(self, polygon):
        self.statements.append(AMPolygonPrimitive.from_primitive(polygon))

    def _render_thermal(self, thermal):
        pass


class Rs274xContext(GerberContext):

    def __init__(self, settings):
        GerberContext.__init__(self)
        self.comments = []
        self.header = []
        self.body = []
        self.end = [EofStmt()]

        # Current values so we know if we have to execute
        # moves, levey changes before anything else
        self._level_polarity = None
        self._pos = (None, None)
        self._func = None
        self._quadrant_mode = None
        self._dcode = None

        # Primarily for testing and comarison to files, should we write
        # flashes as a single statement or a move plus flash? Set to true
        # to do in a single statement. Normally this can be false
        self.condensed_flash = True

        # When closing a region, force a D02 staement to close a region.
        # This is normally not necessary because regions are closed with a G37
        # staement, but this will add an extra statement for doubly close
        # the region
        self.explicit_region_move_end = False

        self._next_dcode = 10
        self._rects = {}
        self._circles = {}
        self._obrounds = {}
        self._polygons = {}
        self._macros = {}

        self._i_none = 0
        self._j_none = 0

        self.settings = settings

        self._start_header(settings)

    def _start_header(self, settings):
        self.header.append(FSParamStmt.from_settings(settings))
        self.header.append(MOParamStmt.from_units(settings.units))

    def _simplify_point(self, point):
        return (point[0] if point[0] != self._pos[0] else None, point[1] if point[1] != self._pos[1] else None)

    def _simplify_offset(self, point, offset):

        if point[0] != offset[0]:
            xoffset = point[0] - offset[0]
        else:
            xoffset = self._i_none

        if point[1] != offset[1]:
            yoffset = point[1] - offset[1]
        else:
            yoffset = self._j_none

        return (xoffset, yoffset)

    @property
    def statements(self):
        return self.comments + self.header + self.body + self.end

    def set_bounds(self, bounds, *args, **kwargs):
        pass

    def paint_background(self):
        pass

    def _select_aperture(self, aperture):

        # Select the right aperture if not already selected
        if aperture:
            if isinstance(aperture, Circle):
                aper = self._get_circle(aperture.diameter, aperture.hole_diameter, aperture.hole_width, aperture.hole_height)
            elif isinstance(aperture, Rectangle):
                aper = self._get_rectangle(aperture.width, aperture.height)
            elif isinstance(aperture, Obround):
                aper = self._get_obround(aperture.width, aperture.height)
            elif isinstance(aperture, AMGroup):
                aper = self._get_amacro(aperture)
            else:
                raise NotImplementedError('Line with invalid aperture type')

            if aper.d != self._dcode:
                self.body.append(ApertureStmt(aper.d))
                self._dcode = aper.d

    def pre_render_primitive(self, primitive):

        if hasattr(primitive, 'comment'):
            self.body.append(CommentStmt(primitive.comment))

    def _render_line(self, line, color, default_polarity='dark'):

        self._select_aperture(line.aperture)

        self._render_level_polarity(line, default_polarity)

        # Get the right function
        if self._func != CoordStmt.FUNC_LINEAR:
            func = CoordStmt.FUNC_LINEAR
        else:
            func = None
        self._func = CoordStmt.FUNC_LINEAR

        if self._pos != line.start:
            self.body.append(CoordStmt.move(func, self._simplify_point(line.start)))
            self._pos = line.start
            # We already set the function, so the next command doesn't require that
            func = None

        point = self._simplify_point(line.end)

        # In some files, we see a lot of duplicated ponts, so omit those
        if point[0] != None or point[1] != None:
            self.body.append(CoordStmt.line(func, self._simplify_point(line.end)))
            self._pos = line.end
        elif func:
            self.body.append(CoordStmt.mode(func))

    def _render_arc(self, arc, color, default_polarity='dark'):

        # Optionally set the quadrant mode if it has changed:
        if arc.quadrant_mode != self._quadrant_mode:

            if arc.quadrant_mode != 'multi-quadrant':
                self.body.append(QuadrantModeStmt.single())
            else:
                self.body.append(QuadrantModeStmt.multi())

            self._quadrant_mode = arc.quadrant_mode

        # Select the right aperture if not already selected
        self._select_aperture(arc.aperture)

        self._render_level_polarity(arc, default_polarity)

        # Find the right movement mode. Always set to be sure it is really right
        dir = arc.direction
        if dir == 'clockwise':
            func = CoordStmt.FUNC_ARC_CW
            self._func = CoordStmt.FUNC_ARC_CW
        elif dir == 'counterclockwise':
            func = CoordStmt.FUNC_ARC_CCW
            self._func = CoordStmt.FUNC_ARC_CCW
        else:
            raise ValueError('Invalid circular interpolation mode')

        if self._pos != arc.start:
            # TODO I'm not sure if this is right
            self.body.append(CoordStmt.move(CoordStmt.FUNC_LINEAR, self._simplify_point(arc.start)))
            self._pos = arc.start

        center = self._simplify_offset(arc.center, arc.start)
        end = self._simplify_point(arc.end)
        self.body.append(CoordStmt.arc(func, end, center))
        self._pos = arc.end

    def _render_region(self, region, color):

        self._render_level_polarity(region)

        self.body.append(RegionModeStmt.on())

        for p in region.primitives:

            # Make programmatically generated primitives within a region with
            # unset level polarity inherit the region's level polarity
            if isinstance(p, Line):
                self._render_line(p, color, default_polarity=region.level_polarity)
            else:
                self._render_arc(p, color, default_polarity=region.level_polarity)

        if self.explicit_region_move_end:
            self.body.append(CoordStmt.move(None, None))

        self.body.append(RegionModeStmt.off())

    def _render_level_polarity(self, obj, default='dark'):
        obj_polarity = obj.level_polarity if obj.level_polarity is not None else default
        if obj_polarity != self._level_polarity:
            self._level_polarity = obj_polarity
            self.body.append(LPParamStmt('LP', obj_polarity))

    def _render_flash(self, primitive, aperture):

        self._render_level_polarity(primitive)

        if aperture.d != self._dcode:
            self.body.append(ApertureStmt(aperture.d))
            self._dcode = aperture.d

        if self.condensed_flash:
            self.body.append(CoordStmt.flash(self._simplify_point(primitive.position)))
        else:
            self.body.append(CoordStmt.move(None, self._simplify_point(primitive.position)))
            self.body.append(CoordStmt.flash(None))

        self._pos = primitive.position

    def _get_circle(self, diameter, hole_diameter=None, hole_width=None,
                    hole_height=None, dcode = None):
        '''Define a circlar aperture'''

        key = (diameter, hole_diameter, hole_width, hole_height)
        aper = self._circles.get(key, None)

        if not aper:
            if not dcode:
                dcode = self._next_dcode
                self._next_dcode += 1
            else:
                self._next_dcode = max(dcode + 1, self._next_dcode)

            aper = ADParamStmt.circle(dcode, diameter, hole_diameter, hole_width, hole_height)
            self._circles[(diameter, hole_diameter, hole_width, hole_height)] = aper
            self.header.append(aper)

        return aper

    def _render_circle(self, circle, color):

        aper = self._get_circle(circle.diameter, circle.hole_diameter, circle.hole_width, circle.hole_height)
        self._render_flash(circle, aper)

    def _get_rectangle(self, width, height, hole_diameter=None, hole_width=None,
                       hole_height=None, dcode = None):
        '''Get a rectanglar aperture. If it isn't defined, create it'''

        key = (width, height, hole_diameter, hole_width, hole_height)
        aper = self._rects.get(key, None)

        if not aper:
            if not dcode:
                dcode = self._next_dcode
                self._next_dcode += 1
            else:
                self._next_dcode = max(dcode + 1, self._next_dcode)

            aper = ADParamStmt.rect(dcode, width, height, hole_diameter, hole_width, hole_height)
            self._rects[(width, height, hole_diameter, hole_width, hole_height)] = aper
            self.header.append(aper)

        return aper

    def _render_rectangle(self, rectangle, color):

        aper = self._get_rectangle(rectangle.width, rectangle.height,
                                   rectangle.hole_diameter,
                                   rectangle.hole_width, rectangle.hole_height)
        self._render_flash(rectangle, aper)

    def _get_obround(self, width, height, hole_diameter=None, hole_width=None,
                     hole_height=None, dcode = None):

        key = (width, height, hole_diameter, hole_width, hole_height)
        aper = self._obrounds.get(key, None)

        if not aper:
            if not dcode:
                dcode = self._next_dcode
                self._next_dcode += 1
            else:
                self._next_dcode = max(dcode + 1, self._next_dcode)

            aper = ADParamStmt.obround(dcode, width, height, hole_diameter, hole_width, hole_height)
            self._obrounds[key] = aper
            self.header.append(aper)

        return aper

    def _render_obround(self, obround, color):

        aper = self._get_obround(obround.width, obround.height,
                                 obround.hole_diameter, obround.hole_width,
                                 obround.hole_height)
        self._render_flash(obround, aper)

    def _render_polygon(self, polygon, color):

        aper = self._get_polygon(polygon.radius, polygon.sides,
                                 polygon.rotation, polygon.hole_diameter,
                                 polygon.hole_width, polygon.hole_height)
        self._render_flash(polygon, aper)

    def _get_polygon(self, radius, num_vertices, rotation, hole_diameter=None,
                     hole_width=None, hole_height=None, dcode = None):

        key = (radius, num_vertices, rotation, hole_diameter, hole_width, hole_height)
        aper = self._polygons.get(key, None)

        if not aper:
            if not dcode:
                dcode = self._next_dcode
                self._next_dcode += 1
            else:
                self._next_dcode = max(dcode + 1, self._next_dcode)

            aper = ADParamStmt.polygon(dcode, radius * 2, num_vertices,
                                       rotation, hole_diameter, hole_width,
                                       hole_height)
            self._polygons[key] = aper
            self.header.append(aper)

        return aper

    def _render_drill(self, drill, color):
        raise ValueError('Drills are not valid in RS274X files')

    def _hash_amacro(self, amgroup):
        '''Calculate a very quick hash code for deciding if we should even check AM groups for comparision'''

        # We always start with an X because this forms part of the name
        # Basically, in some cases, the name might start with a C, R, etc. That can appear
        # to conflict with normal aperture definitions. Technically, it shouldn't because normal
        # aperture definitions should have a comma, but in some cases the commit is omitted
        hash = 'X'
        for primitive in amgroup.primitives:

            hash += primitive.__class__.__name__[0]

            bbox = primitive.bounding_box
            hash += str((bbox[0][1] - bbox[0][0]) * 100000)[0:2]
            hash += str((bbox[1][1] - bbox[1][0]) * 100000)[0:2]

            if hasattr(primitive, 'primitives'):
                hash += str(len(primitive.primitives))

            if isinstance(primitive, Rectangle):
                hash += str(primitive.width * 1000000)[0:2]
                hash += str(primitive.height * 1000000)[0:2]
            elif isinstance(primitive, Circle):
                hash += str(primitive.diameter * 1000000)[0:2]

            if len(hash) > 20:
                # The hash might actually get quite complex, so stop before
                # it gets too long
                break

        return hash

    def _get_amacro(self, amgroup, dcode = None):
        # Macros are a little special since we don't have a good way to compare them quickly
        # but in most cases, this should work

        hash = self._hash_amacro(amgroup)
        macro = None
        macroinfo = self._macros.get(hash, None)

        if macroinfo:

            # We have a definition, but check that the groups actually are the same
            for macro in macroinfo:

                # Macros should have positions, right? But if the macro is selected for non-flashes
                # then it won't have a position. This is of course a bad gerber, but they do exist
                if amgroup.position:
                    position = amgroup.position
                else:
                    position = (0, 0)

                offset = (position[0] - macro[1].position[0], position[1] - macro[1].position[1])
                if amgroup.equivalent(macro[1], offset):
                    break
                macro = None

        # Did we find one in the group0
        if not macro:
            # This is a new macro, so define it
            if not dcode:
                dcode = self._next_dcode
                self._next_dcode += 1
            else:
                self._next_dcode = max(dcode + 1, self._next_dcode)

            # Create the statements
            # TODO
            amrenderer = AMGroupContext()
            statement = amrenderer.render(amgroup, hash)

            self.header.append(statement)

            aperdef = ADParamStmt.macro(dcode, hash)
            self.header.append(aperdef)

            # Store the dcode and the original so we can check if it really is the same
            # If it didn't have a postition, set it to 0, 0
            if amgroup.position == None:
                amgroup.position = (0, 0)
            macro = (aperdef, amgroup)

            if macroinfo:
                macroinfo.append(macro)
            else:
                self._macros[hash] = [macro]

        return macro[0]

    def _render_amgroup(self, amgroup, color):

        aper = self._get_amacro(amgroup)
        self._render_flash(amgroup, aper)

    def _render_inverted_layer(self):
        pass

    def new_render_layer(self):
        # TODO Might need to implement this
        pass

    def flatten(self):
        # TODO Might need to implement this
        pass

    def dump(self):
        """Write the rendered file to a StringIO steam"""
        statements = map(lambda stmt: stmt.to_gerber(self.settings), self.statements)
        stream = StringIO()
        for statement in statements:
            stream.write(statement + '\n')

        return stream
