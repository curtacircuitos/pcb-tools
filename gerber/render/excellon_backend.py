
from .render import GerberContext
from ..excellon import DrillSlot
from ..excellon_statements import *

class ExcellonContext(GerberContext):

    MODE_DRILL = 1
    MODE_SLOT =2

    def __init__(self, settings):
        GerberContext.__init__(self)

        # Statements that we write
        self.comments = []
        self.header = []
        self.tool_def = []
        self.body_start = [RewindStopStmt()]
        self.body = []
        self.start = [HeaderBeginStmt()]

        # Current tool and position
        self.handled_tools = set()
        self.cur_tool = None
        self.drill_mode = ExcellonContext.MODE_DRILL
        self.drill_down = False
        self._pos = (None, None)

        self.settings = settings

        self._start_header()
        self._start_comments()

    def _start_header(self):
        """Create the header from the settings"""

        self.header.append(UnitStmt.from_settings(self.settings))

        if self.settings.notation == 'incremental':
            raise NotImplementedError('Incremental mode is not implemented')
        else:
            self.body.append(AbsoluteModeStmt())

    def _start_comments(self):

        # Write the digits used - this isn't valid Excellon statement, so we write as a comment
        self.comments.append(CommentStmt('FILE_FORMAT=%d:%d' % (self.settings.format[0], self.settings.format[1])))

    def _get_end(self):
        """How we end depends on our mode"""

        end = []

        if self.drill_down:
            end.append(RetractWithClampingStmt())
            end.append(RetractWithoutClampingStmt())

        end.append(EndOfProgramStmt())

        return end

    @property
    def statements(self):
        return self.start + self.comments + self.header + self.body_start + self.body + self._get_end()

    def set_bounds(self, bounds, *args, **kwargs):
        pass

    def paint_background(self):
        pass

    def _render_line(self, line, color):
        raise ValueError('Invalid Excellon object')
    def _render_arc(self, arc, color):
        raise ValueError('Invalid Excellon object')

    def _render_region(self, region, color):
        raise ValueError('Invalid Excellon object')

    def _render_level_polarity(self, region):
        raise ValueError('Invalid Excellon object')

    def _render_circle(self, circle, color):
        raise ValueError('Invalid Excellon object')

    def _render_rectangle(self, rectangle, color):
        raise ValueError('Invalid Excellon object')

    def _render_obround(self, obround, color):
        raise ValueError('Invalid Excellon object')

    def _render_polygon(self, polygon, color):
        raise ValueError('Invalid Excellon object')

    def _simplify_point(self, point):
        return (point[0] if point[0] != self._pos[0] else None, point[1] if point[1] != self._pos[1] else None)

    def _render_drill(self, drill, color):

        if self.drill_mode != ExcellonContext.MODE_DRILL:
            self._start_drill_mode()

        tool = drill.hit.tool
        if not tool in self.handled_tools:
            self.handled_tools.add(tool)
            self.header.append(ExcellonTool.from_tool(tool))

        if tool != self.cur_tool:
            self.body.append(ToolSelectionStmt(tool.number))
            self.cur_tool = tool

        point = self._simplify_point(drill.position)
        self._pos = drill.position
        self.body.append(CoordinateStmt.from_point(point))

    def _start_drill_mode(self):
        """
        If we are not in drill mode, then end the ROUT so we can do basic drilling
        """

        if self.drill_mode == ExcellonContext.MODE_SLOT:

            # Make sure we are retracted before changing modes
            last_cmd = self.body[-1]
            if self.drill_down:
                self.body.append(RetractWithClampingStmt())
                self.body.append(RetractWithoutClampingStmt())
                self.drill_down = False

            # Switch to drill mode
            self.body.append(DrillModeStmt())
            self.drill_mode = ExcellonContext.MODE_DRILL

        else:
            raise ValueError('Should be in slot mode')

    def _render_slot(self, slot, color):

        # Set the tool first, before we might go into drill mode
        tool = slot.hit.tool
        if not tool in self.handled_tools:
            self.handled_tools.add(tool)
            self.header.append(ExcellonTool.from_tool(tool))

        if tool != self.cur_tool:
            self.body.append(ToolSelectionStmt(tool.number))
            self.cur_tool = tool

        # Two types of drilling - normal drill and slots
        if slot.hit.slot_type == DrillSlot.TYPE_ROUT:

            # For ROUT, setting the mode is part of the actual command.

            # Are we in the right position?
            if slot.start != self._pos:
                if self.drill_down:
                    # We need to move into the right position, so retract
                    self.body.append(RetractWithClampingStmt())
                    self.drill_down = False

                # Move to the right spot
                point = self._simplify_point(slot.start)
                self._pos = slot.start
                self.body.append(CoordinateStmt.from_point(point, mode="ROUT"))

            # Now we are in the right spot, so drill down
            if not self.drill_down:
                self.body.append(ZAxisRoutPositionStmt())
                self.drill_down = True

            # Do a linear move from our current position to the end position
            point = self._simplify_point(slot.end)
            self._pos = slot.end
            self.body.append(CoordinateStmt.from_point(point, mode="LINEAR"))

            self.drill_mode = ExcellonContext.MODE_SLOT

        else:
            # This is a G85 slot, so do this in normally drilling mode
            if self.drill_mode != ExcellonContext.MODE_DRILL:
                self._start_drill_mode()

            # Slots don't use simplified points
            self._pos = slot.end
            self.body.append(SlotStmt.from_points(slot.start, slot.end))

    def _render_inverted_layer(self):
        pass
