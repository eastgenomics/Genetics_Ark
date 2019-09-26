#
# Various core functions to be used throughout the project.
#
#
# Kim Brugger (12 May 2016), contact: kbr@brugger.dk

import pprint as pp

def svg_perc_coverage(perc):

    HEIGHT = 12
    WIDTH  = 100
    MARGIN =  1

    WIDTH_DRAW  = WIDTH - 2*MARGIN
    HEIGHT_DRAW = HEIGHT - 2*MARGIN
    MID_HEIGHT  = HEIGHT/2



    x0 = MARGIN
    x1 = WIDTH - MARGIN*2

    y0 = MARGIN
    y1 = HEIGHT - MARGIN*2


    s = ""

    s += "<svg width='%d' height='%d'>" % ( WIDTH, HEIGHT )
#    if ( current is not None) :
#        s += "  <title>%f</title>" % current

    fill_colour = 'red'    
    if ( perc >= 100 ):
        fill_colour = 'green'
    elif ( perc >= 98 ):
        fill_colour = 'yellow'
    elif ( perc >= 90 ):
        fill_colour = 'orange'


    import colorsys
    import struct
    
    colour_value = 0
    MIN_VALUE = 79
    if ( perc >= MIN_VALUE ):
        print(perc)
        colour_value = ( (100 - MIN_VALUE) - ( 100.0-perc ) ) /(100 - MIN_VALUE)*100
        print(colour_value)
        

    hue = colour_value*0.35/100

    rgb = colorsys.hsv_to_rgb(hue, 0.99, 0.99)
    rgb = map(lambda x: int(x*255), rgb)
    hex_colour = "#" + struct.pack('BBB',*rgb).encode('hex')
    s +=  "  <rect x='%f' y='%f' width='%f' height='%f' style='fill:%s;stroke:black;stroke-width:1;opacity:0.7' />" %( x0, y0, x1, y1, hex_colour )
    

    s +=  "</svg> "

    return s



def svg_boxplot( data, current=None):

    HEIGHT = 100
    WIDTH  = 400
    MARGIN =  20
    CIRCLE_DIR = 10


    HEIGHT = 20
    WIDTH  = 100
    MARGIN =  5
    CIRCLE_DIR = 10
    CIRCLE_DIR = (HEIGHT-2*MARGIN)/2

    WIDTH_DRAW  = WIDTH - 2*MARGIN
    HEIGHT_DRAW = HEIGHT - 2*MARGIN
    MID_HEIGHT  = HEIGHT/2

    print(data)

    data = sorted( data )
    mean = sum(data)/len(data)
    q0   = min( data )
    q1   = data[ int(len(data)/4) ]
    q2   = data[ int(len(data)/2) ]
    q3   = data[ int(len(data)*3/4) ]
    q4   = max( data )
    range = q4 - q0

    x1 = WIDTH_DRAW/range*(q1-q0)+MARGIN
    x2 = WIDTH_DRAW/range*(q2-q0)+MARGIN
    x3 = WIDTH_DRAW/range*(q3-q0)+MARGIN

    x0 = (q0-q0)* WIDTH_DRAW / range + MARGIN
    x1 = (q1-q0)* WIDTH_DRAW / range + MARGIN
    x2 = (q2-q0)* WIDTH_DRAW / range + MARGIN
    x3 = (q3-q0)* WIDTH_DRAW / range + MARGIN
    x4 = (q4-q0)* WIDTH_DRAW / range + MARGIN





    s = ""

    s += "<svg width='%d' height='%d'>" % ( WIDTH, HEIGHT )
    if ( current is not None) :
        s += "  <title>%f</title>" % current

    s +=  "  <rect x='%f' y='%f' width='%f' height='%f' style='fill:green;stroke:black;stroke-width:2;opacity:0.9' />" %( x1, MARGIN, x3-x1, HEIGHT_DRAW)
    
    s += "  <line x1='%f' y1='%f' x2='%f' y2='%f' style='stroke:rgb(0,0,0);stroke-width:2' />" % ( MARGIN, MID_HEIGHT, MARGIN+WIDTH_DRAW, MID_HEIGHT)

    s += "  <line x1='%f' y1='%f' x2='%f' y2='%f' style='stroke:rgb(0,0,0);stroke-width:2' />" % ( x2, MARGIN, x2, MARGIN+HEIGHT_DRAW)


    if ( current is not None):
        Xcurrent = (current-q0) * WIDTH_DRAW / range + MARGIN

        if (current < q1 or current > q3 ):
            s += "  <ellipse cx='%f' cy='%f' rx='%f' ry='%f' stroke='black' stroke-width='2' fill='red' />" %( Xcurrent, MID_HEIGHT, CIRCLE_DIR-1, CIRCLE_DIR)
        else:
            s += "  <ellipse cx='%f' cy='%f' rx='%f' ry='%f' stroke='black' stroke-width='2' fill='lightgreen' />" %( Xcurrent, MID_HEIGHT, CIRCLE_DIR-1, CIRCLE_DIR)


    s +=  "</svg> "

    return s



def is_a_number( value ):
    if ( type(value) is not float and  type(value) is not int ):
        return False

    return True



def readable_number( value ):    

    if ( type( value ) is not int and type( value ) is not float):
        return value

    if (value > 1000000000):
        value = "%.2fB" %( value*1.0/ 1000000000)
    elif (value > 1000000):
        value = "%.2fM" %( value*1.0/ 1000000)
    elif (value > 1000):
        value = "%.2fK" %( value*1.0/ 1000)
    elif ( type( value ) is float ):
        value = "%.2f" % value

    return value

