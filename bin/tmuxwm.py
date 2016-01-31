#!/usr/bin/env python

"""
TODO:

* search window/process by name
* search by pointer
* parse tmux lsw data
* detect tmux interaction
"""

from sh import xwininfo, xdotool, tmux
import os
import re

def get_current_window_id():
    return os.environ.get( 'WINDOWID' )

def get_window_position( window_id ):
    """
     Absolute upper-left X:  1
     Absolute upper-left Y:  30
     Relative upper-left X:  1
     Relative upper-left Y:  15
     Width: 1918
     Height: 1148
     Depth: 24
     Visual: 0x21
     Visual Class: TrueColor
     Border width: 0
     Class: InputOutput
     Colormap: 0x20 (installed)
     Bit Gravity State: NorthWestGravity
     Window Gravity State: NorthWestGravity
     Backing Store State: NotUseful
     Save Under State: no
     Map State: IsViewable
     Override Redirect State: no
     Corners:  +1+30  -1+30  -1-22  +1-22
     -geometry 319x88+0+15
    
    """
    output = xwininfo("-id", window_id )
    
    data = {
        'pos_x': 'Absolute upper-left X',
        'pos_y': 'Absolute upper-left Y',
        'width': 'Width',
        'height': 'Height',
    }

    result = {}
    for line in output.splitlines():
        if not ':' in line:
            continue
        field_name, field_value = line.strip().split(':', 1)
        for k, v in data.items():
            if v == field_name:
                result[k] = int(field_value)
    return result

def move_window_to_pane( pane_number, window_id ):
    pass

def get_current_tmux_pane( ):
    window_number = None
    pane_number = None
    for line in tmux("lsw"):
        if '(active)' in line:
            window_number = int( line.split(':',1)[0] )
    for line in tmux("lsp"):
        if '(active)' in line:
            pane_number = int( line.split(':',1)[0] )
    return window_number, pane_number

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def parse_tmux_layout_line( layout ):

    # add pane number
    layout = re.sub(r'(?<!,){', ',{', layout.replace('[','{').replace(']','}') )

    pane_at_pos = {}
    p = re.compile('{[^{}]*}')

    while True:
        m = p.search(layout)
        if m:
            start = m.start()
            for pane in chunks( m.group()[1:-1].split(','), 4 ):
                pane_at_pos[ start ] = pane
                start += len( ",".join( pane ) ) + 1
            start, stop = m.span()
            layout = layout[:start] + 'x'*(stop-start) + layout[stop:]
        else:
            break

    answer = []
    for n, d in sorted( pane_at_pos.items(), key=lambda x:x[0] ):
        if 'xxxxx' not in d[3]:
            pane_data = { 'geom': d[0], 'x': int(d[1]), 'y': int(d[2]) }
            (width,height) = pane_data['geom'].split('x', 1)

            pane_data[ 'height' ] = int(height)
            pane_data[ 'width' ] = int(width)
            answer += [ pane_data ]

    return answer

def parse_tmux_layout():
    # FIXME:
    # this re does not care about recursion, although it should
    p = re.compile(r'[[]layout [^,]*,(.*)[]]')

    parsed_layout = {}
    for line in tmux("lsw").splitlines():
        window_number, layout_line = line.split(':', 1)
        window_number = int( window_number )
        m = p.search( layout_line )
        if m:
            parsed_layout[window_number] = parse_tmux_layout_line( m.groups(1)[0] )

    return parsed_layout


def get_tmux_pane_pos_col_row( window, pane ):
    tmux_layout = parse_tmux_layout()
    return tmux_layout[window][pane]

def find_wid_by_name( name ):
    answer = xdotool('search', '--name', name )
    for line in answer.splitlines():
        return line

def move_window_to_pane( name, pane=None ):
    """
    If pane is None, use the current pane.
    """
    term_cols = 319
    term_rows = 87

    if pane is None:
        pane = get_current_tmux_pane()
    pane_pos = get_tmux_pane_pos_col_row( *pane )
    pane_col_pos = pane_pos['x']
    pane_row_pos = pane_pos['y']
    pane_cols = pane_pos['width']
    pane_rows = pane_pos['height']

    terminal_position = get_window_position( get_current_window_id() )
    width = terminal_position['width']
    height = terminal_position['height']
    pos_x = terminal_position['pos_x']
    pos_y = terminal_position['pos_y']

    delta_x = width / term_cols
    delta_y = height / term_rows

    start_x = delta_x * pane_col_pos + pos_x
    start_y = delta_y * pane_row_pos + pos_y
    size_x  = delta_x * pane_cols
    size_y  = delta_y * pane_rows

    wid = find_wid_by_name( name )
    if wid:
        xdotool( "windowsize", wid, size_x, size_y, "windowmove", wid, start_x, start_y )



#print get_window_position( get_current_window_id() )
#get_tmux_pane_pos( 0 )

#print parse_tmux_layout(  )
move_window_to_pane( "Nieuw tabblad" )
