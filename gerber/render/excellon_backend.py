
from .render import GerberContext
from ..excellon_statements import *

class ExcellonContext(GerberContext):
    
    def __init__(self, settings):
        GerberContext.__init__(self)
        self.comments = []
        self.header = []
        self.tool_def = []
        self.body = []
        self.end = [EndOfProgramStmt()]
        
        self.handled_tools = set()
        self.cur_tool = None
        self.pos = (None, None)
        
        self.settings = settings

        self._start_header(settings)
        
    def _start_header(self, settings):
        pass
        
    @property
    def statements(self):
        return self.comments + self.header + self.body + self.end
        
    def set_bounds(self, bounds):
        pass
    
    def _paint_background(self):
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
        
        if not drill in self.handled_tools:
            self.tool_def.append(drill.tool)
    
        if drill.tool != self.cur_tool:
            self.body.append(ToolSelectionStmt(drill.tool.number))
            
        point = self._simplify_point(drill.position)
        self._pos = drill.position
        self.body.append(CoordinateStmt.from_point())

    def _render_inverted_layer(self):
        pass
        