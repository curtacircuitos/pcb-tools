
# Gerber (RS-274X or Extended Gerber) is a bilevel, resolution independent image format.

# // graphic objects
# // draw: line segment, thickness, round or square line endings. (solid circle and rectangule apertures only)
# // arc: circular arc, thickness, round endings. (solid circle standard aperture only)
# // flash: replication of a given apertura (shape)
# // region: are defined by a countour (linear/arc segments.)
#
# // draw/arc: can have zero length (just flash the aperture)
# // flash: any aperture can be flashed
#
# // operation codes operates on coordinate data blocks. each operation code is for one coordinate data block pair and vice-versa.
# // D01: stroke an aperture from current point to coordinate pair. region mode off. lights-on move.
# // D02: move current point to this coordinate pair
# // D03: flash current aperture at this coordinate pair.
#
# // graphics state
# // all state controlled by codes and parameters, except current point
# //
# // state				fixed?		initial value
# // coordinate format	fixed		undefined
# // unit					fixed		undefined
# // image polarity		fixed		positive
# // steps/repeat			variable	1,1,-,-
# // level polarity		variable	dark
# // region mode			variable	off
# // current aperture		variable	undefined
# // quadrant mode		variable	undefined
# // interpolation mode	variable	undefined
# // current point		variable	(0,0)
#
# // attributes: metadata, both standard and custom. No change on image.
#
# // G01: linear
# // G04: comment
# // M02: end of file
# // D: select aperture
# // G75: multi quadrant mode (circles)
# // G36: region begin
# // G37: region end
#
# // [G01] [Xnnfffff] [Ynnffff] D01*
#
# // ASCII 32-126, CR LF.
# // * end-of-block
# // % parameer delimiter
# // , field separator
# // <space> only in comments
# // case sensitive
#
# // int: +/- 32 bit signed
# // decimal: +/- digits
# // names: [a-zA-Z_$]{[a-zA-Z_$0-9]+} (255)
# // strings: [a-zA-Z0-9_+-/!?<>”’(){}.\|&@# ]+ (65535)
#
# // data block: end in *
# // statement: one or more data block, if contain parameters starts and end in % (parameter statement)
# // statement: [%]<Data Block>{<Data Block>}[%]
# // statements: function code, coordinate data, parameters
#
# // function code: operation codes (D01..) or code that set state.
# // function codes applies before operation codes act on coordinates
#
# // coordinate data: <Coordinate data>: [X<Number>][Y<Number>][I<Number>][J<Number>](D01|D02|D03)
# // offsets are not modal
#
# // parameter: %Parameter code<required modifiers>[optional modifiers]*%
# // code: 2 characters
#
# // parameters can have line separators: %<Parameter>{{<Line separator>}<Parameter>}%
#
# // function code: (GDM){1}[number], parameters: [AZ]{2}