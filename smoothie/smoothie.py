from . import nc
import datetime

now = datetime.datetime.now()


class Creator(nc.Creator):

    def __init__(self):
        nc.Creator.__init__(self)
        self.blocknums = False
        self.x = 0
        self.y = 0
        self.z = 0
        self.n = 0
        self.f = 0
        self.fv = 0
        self.last_f = 0
        self.in_drill_cycle = False

    def writecmd(self, s):
        if self.blocknums:
            self.write('N{0} '.format(self.n))
            self.n += 1

        self.file.write(s)

        self.file.write('\n')

    def program_begin(self, id, comment):
        self.comment('Created with Smoothieware post processor')
        self.comment(str(now.strftime("%Y/%m/%d %H:%M")))

    def program_end(self):
        self.comment('program end')
        self.write('M5 ; spindle off')

    def comment(self, text):
        self.write(';{}\n'.format(text))

    def unsupported(self, text):
        self.comment('not supported: {0}'.format(text))

    def flush_nc(self):
        pass

    #
    # Settings

    def imperial(self):
        self.writecmd('G20')

    def metric(self):
        self.writecmd('G21')

    def absolute(self):
        self.writecmd('G90')

    def incremental(self):
        self.writecmd('G91')

    def polar(self, on=True):
        self.unsupported('set polar coordinates')

    def set_plane(self, plane):
        """Set plane"""
        if plane == 0:
            self.writecmd('G17')
        elif plane == 1:
            self.writecmd('G18')
        elif plane == 3:
            self.writecmd('G19')

    def set_temporary_origin(
            self, x=None, y=None, z=None, a=None, b=None, c=None):
        """Set temporary origin G92"""
        pass

    def remove_temporary_origin(self):
        """Remote temporary origin G92.1"""
        pass

    # not supported by Smoothieware as of 2015-03-18

    #
    # Subprograms

    def sub_begin(self, id, name=''):
        """Begin a subprogram"""
        pass

    def sub_call(self, id):
        """Call a subprogram"""
        pass

    def sub_end(self):
        """Return from a subprogram"""
        pass
    #
    # Tools

    def tool_defn(self, id, name='', radius=None, length=None, gradient=None):
        self.unsupported('tool_defn')

    def tool_change(self, id):
        self.unsupported('tool_change')

    def offset_radius(self, id, radius=None):
        self.unsupported('offset_radius')

    def offset_length(self, id, length=None):
        self.unsupported('offset_length')

    #
    # Datums

    def datum_shift(self, x=None, y=None, z=None, a=None, b=None, c=None):
        self.unsupported('datum_shift')

    def datum_set(self, x=None, y=None, z=None, a=None, b=None, c=None):
        self.unsupported('datum_set')

    def workplane(self, id):
        self.unsupported('workplane')

    def clearanceplane(self, z=None):
        self.unsupported('clearanceplane')

    #
    # APT360 like Transformation Definitions
    # These definitions were created while looking at Irvin Kraal's book on APT
    # - Numerical Control Progamming in APT - page 211

    def matrix(self, a1=None, b1=None, c1=None, a2=None,
               b2=None, c2=None, a3=None, b3=None, c3=None):
        """Create a matrix for transformations"""
        pass

    def translate(self, x=None, y=None, z=None):
        self.unsupported('translate')

    def rotate(self, xyrot=None, yzrot=None, zxrot=None, angle=None):
        self.unsupported('rotate')

    def scale(self, k=None):
        self.unsupported('scale')

    def matrix_product(self, matrix1=None, matrix2=None):
        self.unsupported('matrix_product')

    def mirror_plane(self, plane1=None, plane2=None, plane3=None):
        self.unsupported('mirror_plane')

    def mirror_line(self, line=None):
        self.unsupported('mirror_line')

    #
    ##  Rates + Modes

    def feedrate(self, f):
        self.f = f

    def feedrate_hv(self, fh, fv):
        """Set the horizontal and vertical feedrates"""
        self.feedrate(fh)
        self.fv = fv

    def spindle(self, s, clockwise=True):
        self.unsupported('spindle control disabled')
        return

        if clockwise:
            cmd = 'M3'
            if s:
                cmd += ' S{}'.format(s)
            self.writecmd(cmd)
        else:
            self.unsupported('counter clock wise spindle rotation')

    def coolant(self, mode=0):
        self.unsupported('coolant')

    def gearrange(self, gear=0):
        self.unsupported('gear range')

    #
    # Moves

    def fmtaxis(self, axis, value):
        return ' {0}{1:.4f}'.format(axis.upper(), value)

    def rapid(self, x=None, y=None, z=None,
              a=None, b=None, c=None,
              u=None, v=None, w=None,
              machine_coordinates=None):

        cmd = 'G0'
        axes = 'xyzabcuvw'

        for axis in axes:
            val = locals()[axis]
            if val is not None:
                cmd += self.fmtaxis(axis, val)

                if axis == 'x':
                    self.x = x
                if axis == 'y':
                    self.y = y

        self.writecmd(cmd)

        if machine_coordinates:
            self.unsupported('machine coordinates of rapid')

    def feed(self, x=None, y=None, z=None):

        cmd = 'G1'
        axes = 'xyz'
        use_vert_feedrate = False

        for axis in axes:
            val = locals()[axis]
            if val is not None:
                if axis == 'x':
                    self.x = x
                if axis == 'y':
                    self.y = y

                if axis == 'z':
                    if abs(val - getattr(self, axis)) > 1e-10:
                        # if Z movement is present
                        self.comment('zdiff %f != %f' % (val, self.z))
                        use_vert_feedrate = True
                        #continue
                    self.z = z

                cmd += self.fmtaxis(axis, val)

        if use_vert_feedrate:
            self.last_f = self.fv
            cmd += ' F{0}'.format(self.fv)
        elif self.last_f != self.f:
            self.last_f = self.f
            cmd += ' F{0}'.format(self.f)

        self.writecmd(cmd)

    def arc(self, cw=True, x=None, y=None, z=None,
            i=None, j=None, k=None, r=None):

        if cw:
            cmd = 'G2'
        else:
            cmd = 'G3'

        axes = 'xyzij'  # kr' unsupported

        if i is not None:
            i -= self.x

        if j is not None:
            j -= self.y

        for axis in axes:
            val = locals()[axis]
            if val is not None:
                cmd += self.fmtaxis(axis, val)

                if axis == 'x':
                    self.x = x
                if axis == 'y':
                    self.y = y

        if self.last_f != self.f:
            self.last_f = self.f
            cmd += ' F{0}'.format(self.f)

        self.writecmd(cmd)

    def arc_cw(self, *args):
        self.arc(True, *args)

    def arc_ccw(self, *args):
        self.arc(False, *args)

    def dwell(self, t):
        self.writecmd('G4 P{0}'.format(t))

    def rapid_home(self, x=None, y=None, z=None,
                   a=None, b=None, c=None, u=None, v=None, w=None):

        self.unsupported('rapid_home')

    def rapid_unhome(self):
        self.unsupported('rapid_unhome')

    def set_machine_coordinates(self):
        self.unsupported('set_machine_coordinates')

    #
    # Cutter radius compensation

    def use_CRC(self):
        return False

    #
    # Cycles

    def pattern(self):
        pass

    def pocket(self):
        pass

    def profile(self):
        pass

    def drill(self, x=None, y=None, z=None, depth=None, standoff=None,
              dwell=None, peck_depth=None, retract_mode=None, spindle_mode=None):

        if not self.in_drill_cycle:
            self.writecmd('G98 ; retract to Z plane')
            self.in_drill_cycle = True

        cmd = 'G81'
        axes = 'xyz'

        for axis in axes:
            val = locals()[axis]
            if val is not None:
                if axis == 'z':
                    val = z - depth

                cmd += self.fmtaxis(axis, val)

        # G81 R2.00000 Z-2.50000 F90.00000 Y15.11869 X29.6419
        self.writecmd(cmd)

    def tap(self, x=None, y=None, z=None,
            zretract=None, depth=None, standoff=None, dwell_bottom=None,
            pitch=None, stoppos=None,
            spin_in=None, spin_out=None, tap_mode=None, direction=None):

        self.unsupported('tap')

    def bore(self, x=None, y=None, z=None,
             zretract=None, depth=None, standoff=None, dwell_bottom=None,
             feed_in=None, feed_out=None, stoppos=None,
             shift_back=None, shift_right=None, backbore=False, stop=False):

        self.unsupported('bore')

    def end_canned_cycle(self):
        if self.in_drill_cycle:
            self.writecmd('G80')
            self.in_drill_cycle = False

    #
    # Misc

    def insert(self, text):
        self.unsupported('insert')

    def block_delete(self, on=False):
        self.unsupported('block_delete')

    def variable(self, id):
        self.unsupported('variable')

    def variable_set(self, id, value):
        self.unsupported('variable_set')

    def probe_linear_centre_outside(self, x1=None, y1=None,
                                    depth=None, x2=None, y2=None):

        self.unsupported('probe_linear_centre_outside')

    def probe_single_point(self,
                           point_along_edge_x=None, point_along_edge_y=None,
                           depth=None,
                           retracted_point_x=None, retracted_point_y=None,
                           destination_point_x=None, destination_point_y=None,
                           intersection_variable_x=None,
                           intersection_variable_y=None,
                           probe_offset_x_component=None,
                           probe_offset_y_component=None):

        self.unsupported('probe_single_point')

    def probe_downward_point(self, x=None, y=None,
                             depth=None, intersection_variable_z=None):

        self.unsupported('probe_downward_point')

    def report_probe_results(self, x1=None, y1=None, z1=None,
                             x2=None, y2=None, z2=None,
                             x3=None, y3=None, z3=None,
                             x4=None, y4=None, z4=None,
                             x5=None, y5=None, z5=None,
                             x6=None, y6=None, z6=None, xml_file_name=None):

        self.unsupported('report_probe_results')

    def open_log_file(self, xml_file_name=None):
        pass

    def log_coordinate(self, x=None, y=None, z=None):
        pass

    def log_message(self, message=None):
        pass

    def close_log_file(self):
        pass

    def rapid_to_midpoint(self, x1=None, y1=None, z1=None,
                          x2=None, y2=None, z2=None):

        self.unsupported('rapid_to_midpoint')

    def rapid_to_intersection(self, x1, y1, x2, y2, x3, y3, x4, y4,
                              intersection_x, intersection_y,
                              ua_numerator, ua_denominator,
                              ua, ub_numerator, ub):

        self.unsupported('rapid_to_intersection')

    def rapid_to_rotated_coordinate(self, x1, y1, x2, y2,
                                    ref_x, ref_y,
                                    x_current, y_current,
                                    x_final, y_final):

        self.unsupported('rapid_to_rotated_coordinate')

    def set_path_control_mode(self, *args, **kwargs):
        self.unsupported('set_path_control_mode')

nc.creator = Creator()
