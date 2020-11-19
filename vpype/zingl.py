from queue import Queue

from svgelements import *

"""
The Zingl-Bresenham plotting algorithms are from Alois Zingl's "The Beauty of Bresenham's Algorithm"
( http://members.chello.at/easyfilter/bresenham.html ).

In the case of Zingl's work this isn't explicit from his website, however from personal
correspondence "'Free and open source' means you can do anything with it like the MIT licence."

The Zingl-Bresenham algorithms are provided in a static fashion and generate x and y locations.


The Main-class ZinglPlotter simplifies the plotting modifications routines. These are buffered with plottable elements.
These can be submitted as destination graphics commands, or by submitting a plot routine. Which may yield either 2 or 
3 value coordinates. These are x, y, and on. Where on is a number between 0 and 1 which designates the on-value. In the
graphics commands the move is given a 0 and all other plots are given a 1. All graphics commands take an optional
on-value. If PPI is enabled, fractional on values are made non-fractional by carrying forward the value of on as a 
factor applied of the total value.

All plots are queued and processed in order. This queueing scheme is threadsafe, and should permit one thread reading
the plot values while another thread adds additional items to the queue. If the queue completely empties any processes
being applied to the plot stream are flushed prior to terminating the iterator.

Provided positions can be gapped or single, with adjacent or distant values. The on value is expected to denote whether
the transition from the current position to the new position should be drawn or not. Values that have an initial value
of zero will remain zero.

* Singles converts input into single positional shifts. This must be done to process the plot stream.
* PPI does pulses per inch carry forward with the given value.
* Dot Length requires any train of on-values must be of at least the proscribed length.
* Shift moves isolated single-on values to be adjacent to other on-values.
* Groups manipulates the output as max-length changeless orthogonal/diagonal positions.

This work is MIT Licensed.
"""


class ZinglPlotter:
    def __init__(self):
        self.flushed = True
        self.current = []
        self.current_on = None
        self.position = 0
        self.queue = Queue()

        self.x = None
        self.y = None

        self.single_default = 0
        self.single_x = None
        self.single_y = None

        self.ppi_total = 0
        self.ppi_enabled = True
        self.ppi = 1000.0
        self.dot_length = 1
        self.dot_left = 0

        self.group_enabled = True
        self.group_x = None
        self.group_y = None
        self.group_on = None
        self.group_dx = 0
        self.group_dy = 0

        self.shift_enabled = False
        self.shift_buffer = []
        self.shift_pixels = 0

    def __iter__(self):
        return self

    def __next__(self):
        """
        Main method of generating the plot stream.

        :return:
        """
        while len(self.current) <= self.position:
            self.current.clear()
            self.position = 0
            if self.queue.empty():
                if self.flushed:
                    raise StopIteration
                self.current.extend(self.process(None))
                self.flushed = True
                if len(self.current) == 0:
                    raise StopIteration
            else:
                plot, self.single_default = self.queue.get()
                self.current.extend(self.process(plot))
        c = self.current[self.position]
        self.position += 1
        return c

    def add_plot(self, plot, on=1):
        """
        Add a given plot to the queue. The plot is unrolled in order to ensure movement to the first position and to
        update the position to the last position.

        :param plot: Plot to be added.
        :param on: Default on-value for this plot if none is provided.
        :return:
        """
        plot = [c for c in plot]
        if len(plot) == 0:
            return
        start = plot[0]
        self.move_to(start[0], start[1])
        self.queue.put((plot, on))
        end = plot[-1]
        self.x = end[0]
        self.y = end[1]
        self.flushed = False

    def add_path(self, path):
        """
        Adds an svgelements path command of segments to the current queue.

        :param path:
        :return:
        """
        if isinstance(path, Path):
            for seg in path:
                self.add_segment(seg)
        else:
            self.add_segment(path)

    def add_segment(self, seg):
        """
        Adds an svgelement pathsegment to as a graphics plot to the current queue.

        :param seg:
        :return:
        """
        if isinstance(seg, Move):
            if seg.start is not None:
                self.move_to(
                    seg.end[0], seg.end[1], start_x=seg.start[0], start_y=seg.start[1]
                )
            else:
                self.move_to(seg.end[0], seg.end[1], start_x=self.x, start_y=self.y)
        elif isinstance(seg, Close):
            self.line_to(seg.end[0], seg.end[1])
        elif isinstance(seg, Line):
            self.line_to(seg.end[0], seg.end[1])
        elif isinstance(seg, QuadraticBezier):
            self.quad_to(seg.control[0], seg.control[1], seg.end[0], seg.end[1])
        elif isinstance(seg, CubicBezier):
            self.curve_to(
                seg.control1[0],
                seg.control1[1],
                seg.control2[0],
                seg.control2[1],
                seg.end[0],
                seg.end[1],
            )
        elif isinstance(seg, Arc):
            self.arc_to(seg)
        else:
            raise ValueError

    def move_to(self, x, y, start_x=None, start_y=None):
        """
        Moves to the given position. If no position is current set, and no start position is given. This exists at the
        destination.
        :param x: x coordinate destination
        :param y: y coordinate destination
        :param start_x: optional start x coordinate.
        :param start_y: optional start y coordinate
        :return:
        """
        if self.x == x and self.y == y:
            return  # We are already there.
        if start_x is None and start_y is None:
            self.queue.put(([[round(x), round(y)]], 0))
        else:
            self.line_to(x, y, 0)
        self.x = x
        self.y = y
        self.flushed = False

    def line_to(self, x, y, on=1):
        """
        Lines to the given position. Appending that to the queue.

        :param x: x coordinate destination
        :param y: y coordinate destination
        :param on: Default on-value for this plot if none is provided.
        :return:
        """
        self.queue.put((ZinglPlotter.plot_line(self.x, self.y, x, y), on))
        self.x = x
        self.y = y
        self.flushed = False

    def curve_to(self, cx0, cy0, cx1, cy1, x, y, on=1):
        """
        Cubic bezier curve to the destination with the given control points.

        :param cx0: first control point x
        :param cy0: first control point y
        :param cx1: second control point x
        :param cy1: second control point y
        :param x: x coordinate destination
        :param y: y coordinate destination
        :param on: Default on-value for this plot if none is provided.
        :return:
        """
        self.queue.put(
            (ZinglPlotter.plot_cubic_bezier(self.x, self.y, cx0, cy0, cx1, cy1, x, y), on)
        )
        self.x = x
        self.y = y
        self.flushed = False

    def quad_to(self, cx, cy, x, y, on=1):
        """
        Quadratic bezier curve to the destination with the given control point.

        :param cx: control point x
        :param cy: control point y
        :param x: x coordinate destination
        :param y: y coordinate destination
        :param on: Default on-value for this plot if none is provided.
        :return:
        """
        self.queue.put((ZinglPlotter.plot_quad_bezier(self.x, self.y, cx, cy, x, y), on))
        self.x = x
        self.y = y
        self.flushed = False

    def arc_to(self, arc, on=1):
        """
        Arc to a given destination.

        :param arc: SVG arc element.
        :param on: Default on-value for this plot if none is provided.
        :return:
        """
        self.queue.put((ZinglPlotter.plot_arc(arc), on))
        end = arc.end
        self.x = end[0]
        self.y = end[1]
        self.flushed = False

    def process(self, plot):
        """
        Converts a series of inputs into a series of outputs. There is not a 1:1 input to output conversion.
        Processes can buffer data and return None. Processes are required to surrender any buffer they have if the
        given sequence ends with, or is None. This flushes out any data.

        If an input sequence still lacks a on-value then the single_default value will be utilized.
        Output sequences are iterables of x, y, on positions.

        :param plot: plottable element that should be wrapped
        :return: generator to produce plottable elements.
        """
        plot = self.single(plot)
        if self.ppi_enabled:
            plot = self.apply_ppi(plot)
        if self.shift_enabled:
            plot = self.shift(plot)
        if self.group_enabled:
            plot = self.group(plot)
        return plot

    def single(self, plot):
        """
        Convert a sequence set of positions into single unit plotted sequences.

        single_default sets the default for any unmarked processes.
        single_x sets the last known x position this routine has encountered.
        single_y sets the last known y position this routine has encountered.

        :param plot: plot generator
        :return:
        """
        if plot is None:
            yield None
        for event in plot:
            if len(event) == 3:
                x, y, on = event
            else:
                x, y = event
                on = self.single_default
            index = 1
            if self.single_x is None:
                self.single_x = x
                index = 0
            if self.single_y is None:
                self.single_y = y
                index = 0
            if x > self.single_x:
                dx = 1
            elif x < self.single_x:
                dx = -1
            else:
                dx = 0
            if y > self.single_y:
                dy = 1
            elif y < self.single_y:
                dy = -1
            else:
                dy = 0
            total_dx = x - self.single_x
            total_dy = y - self.single_y
            if total_dy * dx != total_dx * dy:
                raise ValueError(
                    "Must be uniformly diagonal or orthogonal: (%d, %d) is not."
                    % (total_dx, total_dy)
                )
            count = max(abs(total_dx), abs(total_dy)) + 1
            interpolated = [
                (self.single_x + (i * dx), self.single_y + (i * dy), on)
                for i in range(index, count)
            ]
            self.single_x = x
            self.single_y = y
            for p in interpolated:
                yield p

    def group(self, plot):
        """
        Converts a generated series of single stepped plots into grouped orthogonal/diagonal plots.

        :param plot: single stepped plots to be grouped into orth/diag sequences.
        :return:
        """
        for event in plot:
            if event is None:
                if self.group_x is not None and self.group_y is not None:
                    yield self.group_x, self.group_y, self.group_on
                self.group_dx = 0
                self.group_dy = 0
                return
            x, y, on = event
            if self.group_x is None:
                self.group_x = x
            if self.group_y is None:
                self.group_y = y
            if self.group_on is None:
                self.group_on = on
            if self.group_dx == 0 and self.group_dy == 0:
                self.group_dx = x - self.group_x
                self.group_dy = y - self.group_y
            if self.group_dx != 0 or self.group_dy != 0:
                if (
                    x == self.group_x + self.group_dx
                    and y == self.group_y + self.group_dy
                    and on == self.group_on
                ):
                    # This is an orthogonal/diagonal step along the same path.
                    self.group_x = x
                    self.group_y = y
                    continue
                yield self.group_x, self.group_y, self.group_on
            self.group_dx = x - self.group_x
            self.group_dy = y - self.group_y
            if abs(self.group_dx) > 1 or abs(self.group_dy) > 1:
                # The last step was not valid.
                raise ValueError("dx(%d) or dy(%d) exceeds 1" % (self.group_dx, self.group_dy))
            self.group_x = x
            self.group_y = y
            self.group_on = on

    def apply_ppi(self, plot):
        """
        Converts single stepped plots, to apply PPI.

        Implements PPI power modulation.

        :param plot: generator of single stepped plots
        :return:
        """
        if plot is None:
            yield None
            return
        for event in plot:
            if event is None:
                yield None
                return
            x, y, on = event
            self.ppi_total += self.ppi * on
            if on and self.dot_left > 0:
                self.dot_left -= 1
                on = 1
            else:
                if self.ppi_total >= 1000.0:
                    on = 1
                    self.ppi_total -= 1000.0 * self.dot_length
                    self.dot_left = self.dot_length - 1
                else:
                    on = 0
                if on:
                    self.dot_left = self.dot_length - 1
            yield x, y, on

    def shift(self, plot):
        """
        Tweaks on-values to simplify them into more coherent subsections.

        :param plot: generator of single stepped plots
        :return:
        """
        for event in plot:
            if event is None:
                while len(self.shift_buffer) > 0:
                    self.shift_pixels <<= 1
                    bx, by = self.shift_buffer.pop()
                    bon = (self.shift_pixels >> 3) & 1
                    yield bx, by, bon
                yield None
                return
            x, y, on = event
            self.shift_pixels <<= 1
            if on:
                self.shift_pixels |= 1
            self.shift_pixels &= 0b1111

            self.shift_buffer.insert(0, (x, y))
            if self.shift_pixels == 0b0101:
                self.shift_pixels = 0b0011
            elif self.shift_pixels == 0b1010:
                self.shift_pixels = 0b1100
            if len(self.shift_buffer) >= 4:
                bx, by = self.shift_buffer.pop()
                bon = (self.shift_pixels >> 3) & 1
                yield bx, by, bon

    @staticmethod
    def plot_path(path):
        """
        Default plot routine for svgelements plot objects

        yields x, y, (1/0)

        The 1 and 0 indicates whether that segment is drawn or undrawn within the path.

        :param path: path or segment to plot.
        :return:
        """
        if isinstance(path, Path):
            for seg in path:
                for values in ZinglPlotter.plot_segment(seg):
                    yield values
        else:
            for values in ZinglPlotter.plot_segment(path):
                yield values

    @staticmethod
    def linearize(path, length="1mm", ppi=96):
        path = abs(path)
        distance_in_pixels = Length(length).value(ppi=ppi)
        i = 0
        for seg in path:
            for values in ZinglPlotter.plot_segment(seg):
                if values[2]:
                    if i > distance_in_pixels:
                        yield values[0], values[1]
                        i = -distance_in_pixels
                    i += 1

    @staticmethod
    def plot_segment(seg):
        """
        Plots a given path segment.

        yields x, y, (1/0)

        The 1 and 0 indicates whether that segment is drawn or undrawn within the path.

        :param seg:
        :return:
        """
        if isinstance(seg, Move):
            if seg.start is not None:
                for x, y in ZinglPlotter.plot_line(
                    seg.start[0], seg.start[1], seg.end[0], seg.end[1]
                ):
                    yield x, y, 0
        elif isinstance(seg, Close):
            if seg.start is not None and seg.end is not None:
                for x, y in ZinglPlotter.plot_line(
                    seg.start[0], seg.start[1], seg.end[0], seg.end[1]
                ):
                    yield x, y, 1
        elif isinstance(seg, Line):
            for x, y in ZinglPlotter.plot_line(
                seg.start[0], seg.start[1], seg.end[0], seg.end[1]
            ):
                yield x, y, 1
        elif isinstance(seg, QuadraticBezier):
            for x, y in ZinglPlotter.plot_quad_bezier(
                seg.start[0],
                seg.start[1],
                seg.control[0],
                seg.control[1],
                seg.end[0],
                seg.end[1],
            ):
                yield x, y, 1

        elif isinstance(seg, CubicBezier):
            for x, y in ZinglPlotter.plot_cubic_bezier(
                seg.start[0],
                seg.start[1],
                seg.control1[0],
                seg.control1[1],
                seg.control2[0],
                seg.control2[1],
                seg.end[0],
                seg.end[1],
            ):
                yield x, y, 1
        elif isinstance(seg, Arc):
            for x, y in ZinglPlotter.plot_arc(seg):
                yield x, y, 1
        else:
            raise ValueError

    @staticmethod
    def plot_arc(arc):
        """
        Plots an arc by converting it into a series of cubic bezier curves and plotting those instead.

        :param arc:
        :return:
        """
        # TODO: Should actually plot the arc according to the pixel-perfect standard.
        # TODO: In this case we would plot a Bernstein weighted bezier curve.
        sweep_limit = tau / 12
        arc_required = int(ceil(abs(arc.sweep) / sweep_limit))
        if arc_required == 0:
            return
        slice = arc.sweep / float(arc_required)

        theta = arc.get_rotation()
        rx = arc.rx
        ry = arc.ry
        p_start = arc.start
        current_t = arc.get_start_t()
        x0 = arc.center[0]
        y0 = arc.center[1]
        cos_theta = cos(theta)
        sin_theta = sin(theta)

        for i in range(0, arc_required):
            next_t = current_t + slice

            alpha = sin(slice) * (sqrt(4 + 3 * pow(tan((slice) / 2.0), 2)) - 1) / 3.0

            cos_start_t = cos(current_t)
            sin_start_t = sin(current_t)

            ePrimen1x = -rx * cos_theta * sin_start_t - ry * sin_theta * cos_start_t
            ePrimen1y = -rx * sin_theta * sin_start_t + ry * cos_theta * cos_start_t

            cos_end_t = cos(next_t)
            sin_end_t = sin(next_t)

            p2En2x = x0 + rx * cos_end_t * cos_theta - ry * sin_end_t * sin_theta
            p2En2y = y0 + rx * cos_end_t * sin_theta + ry * sin_end_t * cos_theta
            p_end = (p2En2x, p2En2y)
            if i == arc_required - 1:
                p_end = arc.end

            ePrimen2x = -rx * cos_theta * sin_end_t - ry * sin_theta * cos_end_t
            ePrimen2y = -rx * sin_theta * sin_end_t + ry * cos_theta * cos_end_t

            p_c1 = (p_start[0] + alpha * ePrimen1x, p_start[1] + alpha * ePrimen1y)
            p_c2 = (p_end[0] - alpha * ePrimen2x, p_end[1] - alpha * ePrimen2y)

            for value in ZinglPlotter.plot_cubic_bezier(
                p_start[0], p_start[1], p_c1[0], p_c1[1], p_c2[0], p_c2[1], p_end[0], p_end[1]
            ):
                yield value
            p_start = Point(p_end)
            current_t = next_t

    @staticmethod
    def plot_line(x0, y0, x1, y1):
        """
        Zingl-Bresenham line draw algorithm

        yields x, y
        """
        x0 = int(x0)
        y0 = int(y0)
        x1 = int(x1)
        y1 = int(y1)
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)

        if x0 < x1:
            sx = 1
        else:
            sx = -1
        if y0 < y1:
            sy = 1
        else:
            sy = -1

        err = dx + dy  # error value e_xy

        while True:  # /* loop */
            yield x0, y0
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:  # e_xy+e_y < 0
                err += dy
                x0 += sx
            if e2 <= dx:  # e_xy+e_y < 0
                err += dx
                y0 += sy

    @staticmethod
    def plot_quad_bezier_seg(x0, y0, x1, y1, x2, y2):
        """plot a limited quadratic Bezier segment

        This algorithm can plot curves that do not inflect.

        This is used as part of the general algorithm, which breaks at the inflection point.

        yields x, y
        """
        sx = x2 - x1
        sy = y2 - y1
        xx = x0 - x1
        yy = y0 - y1
        xy = 0  # relative values for checks */
        dx = 0
        dy = 0
        err = 0
        cur = xx * sy - yy * sx  # /* curvature */
        points = None

        assert xx * sx <= 0 and yy * sy <= 0  # /* sign of gradient must not change */

        if sx * sx + sy * sy > xx * xx + yy * yy:  # /* begin with shorter part */
            x2 = x0
            x0 = sx + x1
            y2 = y0
            y0 = sy + y1
            cur = -cur  # /* swap P0 P2 */
            points = []
        if cur != 0:  # /* no straight line */
            xx += sx
            if x0 < x2:
                sx = 1  # /* x step direction */
            else:
                sx = -1  # /* x step direction */
            xx *= sx
            yy += sy
            if y0 < y2:
                sy = 1
            else:
                sy = -1
            yy *= sy  # /* y step direction */
            xy = 2 * xx * yy
            xx *= xx
            yy *= yy  # /* differences 2nd degree */
            if cur * sx * sy < 0:  # /* negated curvature? */
                xx = -xx
                yy = -yy
                xy = -xy
                cur = -cur
            dx = 4.0 * sy * cur * (x1 - x0) + xx - xy  # /* differences 1st degree */
            dy = 4.0 * sx * cur * (y0 - y1) + yy - xy
            xx += xx
            yy += yy
            err = dx + dy + xy  # /* error 1st step */
            while True:
                if points is None:
                    yield int(x0), int(y0)  # /* plot curve */
                else:
                    points.append((int(x0), int(y0)))
                if x0 == x2 and y0 == y2:
                    if points is not None:
                        for plot in reversed(points):
                            yield plot
                    return  # /* last pixel -> curve finished */
                y1 = 2 * err < dx  # /* save value for test of y step */
                if 2 * err > dy:
                    x0 += sx
                    dx -= xy
                    dy += yy
                    err += dy
                    # /* x step */
                if y1 != 0:
                    y0 += sy
                    dy -= xy
                    dx += xx
                    err += dx
                    # /* y step */
                if not (dy < 0 < dx):  # /* gradient negates -> algorithm fails */
                    break
        for plot in ZinglPlotter.plot_line(
            x0, y0, x2, y2
        ):  # /* plot remaining part to end */:
            if points is None:
                yield plot  # /* plot curve */
            else:
                points.append(plot)  # plotLine(x0,y0, x2,y2) #/* plot remaining part to end */
        if points is not None:
            for plot in reversed(points):
                yield plot

    @staticmethod
    def plot_quad_bezier(x0, y0, x1, y1, x2, y2):
        """
        Zingl-Bresenham quad bezier draw algorithm.

        Plot any quadratic Bezier curve

        yields x, y
        """

        x0 = int(x0)
        y0 = int(y0)
        # control points are permitted fractional elements.
        x2 = int(x2)
        y2 = int(y2)
        x = x0 - x1
        y = y0 - y1
        t = x0 - 2 * x1 + x2
        r = 0
        points = None

        if x * (x2 - x1) > 0:  # /* horizontal cut at P4? */
            if y * (y2 - y1) > 0:  # /* vertical cut at P6 too? */
                if abs((y0 - 2 * y1 + y2) / t * x) > abs(y):  # /* which first? */
                    x0 = x2
                    x2 = x + x1
                    y0 = y2
                    y2 = y + y1  # /* swap points */
                    points = []
                    # /* now horizontal cut at P4 comes first */
            t = (x0 - x1) / t
            r = (1 - t) * ((1 - t) * y0 + 2.0 * t * y1) + t * t * y2  # /* By(t=P4) */
            t = (x0 * x2 - x1 * x1) * t / (x0 - x1)  # /* gradient dP4/dx=0 */
            x = floor(t + 0.5)
            y = floor(r + 0.5)
            r = (y1 - y0) * (t - x0) / (x1 - x0) + y0  # /* intersect P3 | P0 P1 */
            for plot in ZinglPlotter.plot_quad_bezier_seg(x0, y0, x, floor(r + 0.5), x, y):
                if points is None:
                    yield plot
                else:
                    points.append(plot)
            r = (y1 - y2) * (t - x2) / (x1 - x2) + y2  # /* intersect P4 | P1 P2 */
            x0 = x1 = x
            y0 = y
            y1 = floor(r + 0.5)  # /* P0 = P4, P1 = P8 */
        if (y0 - y1) * (y2 - y1) > 0:  # /* vertical cut at P6? */
            t = y0 - 2 * y1 + y2
            t = (y0 - y1) / t
            r = (1 - t) * ((1 - t) * x0 + 2.0 * t * x1) + t * t * x2  # /* Bx(t=P6) */
            t = (y0 * y2 - y1 * y1) * t / (y0 - y1)  # /* gradient dP6/dy=0 */
            x = floor(r + 0.5)
            y = floor(t + 0.5)
            r = (x1 - x0) * (t - y0) / (y1 - y0) + x0  # /* intersect P6 | P0 P1 */
            for plot in ZinglPlotter.plot_quad_bezier_seg(x0, y0, floor(r + 0.5), y, x, y):
                if points is None:
                    yield plot
                else:
                    points.append(plot)
            r = (x1 - x2) * (t - y2) / (y1 - y2) + x2  # /* intersect P7 | P1 P2 */
            x0 = x
            x1 = floor(r + 0.5)
            y0 = y1 = y  # /* P0 = P6, P1 = P7 */
        for plot in ZinglPlotter.plot_quad_bezier_seg(
            x0, y0, x1, y1, x2, y2
        ):  # /* remaining part */
            if points is None:
                yield plot
            else:
                points.append(plot)
        if points is not None:
            for plot in reversed(points):
                yield plot

    @staticmethod
    def plot_cubic_bezier_seg(x0, y0, x1, y1, x2, y2, x3, y3):
        """
        Plot limited cubic Bezier segment

        This algorithm can plot curves that do not inflect.

        It is used as part of the general algorithm, which breaks at the infection point(s)

        yields x, y
        """
        second_leg = []
        f = 0
        fx = 0
        fy = 0
        leg = 1
        if x0 < x3:
            sx = 1
        else:
            sx = -1
        if y0 < y3:
            sy = 1  # /* step direction */
        else:
            sy = -1  # /* step direction */
        xc = -abs(x0 + x1 - x2 - x3)
        xa = xc - 4 * sx * (x1 - x2)
        xb = sx * (x0 - x1 - x2 + x3)
        yc = -abs(y0 + y1 - y2 - y3)
        ya = yc - 4 * sy * (y1 - y2)
        yb = sy * (y0 - y1 - y2 + y3)
        ab = 0
        ac = 0
        bc = 0
        cb = 0
        xx = 0
        xy = 0
        yy = 0
        dx = 0
        dy = 0
        ex = 0
        pxy = 0
        EP = 0.01
        # /* check for curve restrains */
        # /* slope P0-P1 == P2-P3 and  (P0-P3 == P1-P2    or  no slope change)
        # if (x1 - x0) * (x2 - x3) < EP and ((x3 - x0) * (x1 - x2) < EP or xb * xb < xa * xc + EP):
        #     return
        # if (y1 - y0) * (y2 - y3) < EP and ((y3 - y0) * (y1 - y2) < EP or yb * yb < ya * yc + EP):
        #     return

        if xa == 0 and ya == 0:  # /* quadratic Bezier */
            # return plot_quad_bezier_seg(x0, y0, (3 * x1 - x0) >> 1, (3 * y1 - y0) >> 1, x3, y3)
            sx = floor((3 * x1 - x0 + 1) / 2)
            sy = floor((3 * y1 - y0 + 1) / 2)  # /* new midpoint */

            for plot in ZinglPlotter.plot_quad_bezier_seg(x0, y0, sx, sy, x3, y3):
                yield plot
            return
        x1 = (x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0) + 1  # /* line lengths */
        x2 = (x2 - x3) * (x2 - x3) + (y2 - y3) * (y2 - y3) + 1

        while True:  # /* loop over both ends */
            ab = xa * yb - xb * ya
            ac = xa * yc - xc * ya
            bc = xb * yc - xc * yb
            ex = ab * (ab + ac - 3 * bc) + ac * ac  # /* P0 part of self-intersection loop? */
            if ex > 0:
                f = 1  # /* calc resolution */
            else:
                f = floor(sqrt(1 + 1024 / x1))  # /* calc resolution */
            ab *= f
            ac *= f
            bc *= f
            ex *= f * f  # /* increase resolution */
            xy = 9 * (ab + ac + bc) / 8
            cb = 8 * (xa - ya)  # /* init differences of 1st degree */
            dx = 27 * (
                8 * ab * (yb * yb - ya * yc) + ex * (ya + 2 * yb + yc)
            ) / 64 - ya * ya * (xy - ya)
            dy = 27 * (
                8 * ab * (xb * xb - xa * xc) - ex * (xa + 2 * xb + xc)
            ) / 64 - xa * xa * (xy + xa)
            # /* init differences of 2nd degree */
            xx = (
                3
                * (
                    3 * ab * (3 * yb * yb - ya * ya - 2 * ya * yc)
                    - ya * (3 * ac * (ya + yb) + ya * cb)
                )
                / 4
            )
            yy = (
                3
                * (
                    3 * ab * (3 * xb * xb - xa * xa - 2 * xa * xc)
                    - xa * (3 * ac * (xa + xb) + xa * cb)
                )
                / 4
            )
            xy = xa * ya * (6 * ab + 6 * ac - 3 * bc + cb)
            ac = ya * ya
            cb = xa * xa
            xy = 3 * (xy + 9 * f * (cb * yb * yc - xb * xc * ac) - 18 * xb * yb * ab) / 8

            if ex < 0:  # /* negate values if inside self-intersection loop */
                dx = -dx
                dy = -dy
                xx = -xx
                yy = -yy
                xy = -xy
                ac = -ac
                cb = -cb  # /* init differences of 3rd degree */
            ab = 6 * ya * ac
            ac = -6 * xa * ac
            bc = 6 * ya * cb
            cb = -6 * xa * cb
            dx += xy
            ex = dx + dy
            dy += xy  # /* error of 1st step */
            try:
                pxy = 0
                fx = fy = f
                while x0 != x3 and y0 != y3:
                    if leg == 0:
                        second_leg.append((x0, y0))  # /* plot curve */
                    else:
                        yield x0, y0  # /* plot curve */
                    while True:  # /* move sub-steps of one pixel */
                        if pxy == 0:
                            if dx > xy or dy < xy:
                                raise StopIteration  # /* confusing */
                        if pxy == 1:
                            if dx > 0 or dy < 0:
                                raise StopIteration  # /* values */
                        y1 = 2 * ex - dy  # /* save value for test of y step */
                        if 2 * ex >= dx:  # /* x sub-step */
                            fx -= 1
                            dx += xx
                            ex += dx
                            xy += ac
                            dy += xy
                            yy += bc
                            xx += ab
                        elif y1 > 0:
                            raise StopIteration
                        if y1 <= 0:  # /* y sub-step */
                            fy -= 1
                            dy += yy
                            ex += dy
                            xy += bc
                            dx += xy
                            xx += ac
                            yy += cb
                        if not (fx > 0 and fy > 0):  # /* pixel complete? */
                            break
                    if 2 * fx <= f:
                        x0 += sx
                        fx += f  # /* x step */
                    if 2 * fy <= f:
                        y0 += sy
                        fy += f  # /* y step */
                    if pxy == 0 and dx < 0 and dy > 0:
                        pxy = 1  # /* pixel ahead valid */
            except StopIteration:
                pass
            xx = x0
            x0 = x3
            x3 = xx
            sx = -sx
            xb = -xb  # /* swap legs */
            yy = y0
            y0 = y3
            y3 = yy
            sy = -sy
            yb = -yb
            x1 = x2
            if not (leg != 0):
                break
            leg -= 1  # /* try other end */
        for plot in ZinglPlotter.plot_line(
            x3, y3, x0, y0
        ):  # /* remaining part in case of cusp or crunode */
            second_leg.append(plot)
        for plot in reversed(second_leg):
            yield plot

    @staticmethod
    def plot_cubic_bezier(x0, y0, x1, y1, x2, y2, x3, y3):
        """
        Zingl-Bresenham cubic bezier draw algorithm

        Plot any quadratic Bezier curve

        yields x, y
        """
        x0 = int(x0)
        y0 = int(y0)
        # control points are permitted fractional elements.
        x3 = int(x3)
        y3 = int(y3)
        n = 0
        i = 0
        xc = x0 + x1 - x2 - x3
        xa = xc - 4 * (x1 - x2)
        xb = x0 - x1 - x2 + x3
        xd = xb + 4 * (x1 + x2)
        yc = y0 + y1 - y2 - y3
        ya = yc - 4 * (y1 - y2)
        yb = y0 - y1 - y2 + y3
        yd = yb + 4 * (y1 + y2)
        fx0 = x0
        fx1 = 0
        fx2 = 0
        fx3 = 0
        fy0 = y0
        fy1 = 0
        fy2 = 0
        fy3 = 0
        t1 = xb * xb - xa * xc
        t2 = 0
        t = [0] * 5
        # /* sub-divide curve at gradient sign changes */
        if xa == 0:  # /* horizontal */
            if abs(xc) < 2 * abs(xb):
                t[n] = xc / (2.0 * xb)  # /* one change */
                n += 1
        elif t1 > 0.0:  # /* two changes */
            t2 = sqrt(t1)
            t1 = (xb - t2) / xa
            if abs(t1) < 1.0:
                t[n] = t1
                n += 1
            t1 = (xb + t2) / xa
            if abs(t1) < 1.0:
                t[n] = t1
                n += 1
        t1 = yb * yb - ya * yc
        if ya == 0:  # /* vertical */
            if abs(yc) < 2 * abs(yb):
                t[n] = yc / (2.0 * yb)  # /* one change */
                n += 1
        elif t1 > 0.0:  # /* two changes */
            t2 = sqrt(t1)
            t1 = (yb - t2) / ya
            if abs(t1) < 1.0:
                t[n] = t1
                n += 1
            t1 = (yb + t2) / ya
            if abs(t1) < 1.0:
                t[n] = t1
                n += 1
        i = 1
        while i < n:  # /* bubble sort of 4 points */
            t1 = t[i - 1]
            if t1 > t[i]:
                t[i - 1] = t[i]
                t[i] = t1
                i = 0
            i += 1
        t1 = -1.0
        t[n] = 1.0  # /* begin / end point */
        for i in range(0, n + 1):  # /* plot each segment separately */
            t2 = t[i]  # /* sub-divide at t[i-1], t[i] */
            fx1 = (
                t1 * (t1 * xb - 2 * xc) - t2 * (t1 * (t1 * xa - 2 * xb) + xc) + xd
            ) / 8 - fx0
            fy1 = (
                t1 * (t1 * yb - 2 * yc) - t2 * (t1 * (t1 * ya - 2 * yb) + yc) + yd
            ) / 8 - fy0
            fx2 = (
                t2 * (t2 * xb - 2 * xc) - t1 * (t2 * (t2 * xa - 2 * xb) + xc) + xd
            ) / 8 - fx0
            fy2 = (
                t2 * (t2 * yb - 2 * yc) - t1 * (t2 * (t2 * ya - 2 * yb) + yc) + yd
            ) / 8 - fy0
            fx3 = (t2 * (t2 * (3 * xb - t2 * xa) - 3 * xc) + xd) / 8
            fx0 -= fx3
            fy3 = (t2 * (t2 * (3 * yb - t2 * ya) - 3 * yc) + yd) / 8
            fy0 -= fy3
            x3 = floor(fx3 + 0.5)
            y3 = floor(fy3 + 0.5)  # /* scale bounds */
            if fx0 != 0.0:
                fx0 = (x0 - x3) / fx0
                fx1 *= fx0
                fx2 *= fx0
            if fy0 != 0.0:
                fy0 = (y0 - y3) / fy0
                fy1 *= fy0
                fy2 *= fy0
            if x0 != x3 or y0 != y3:  # /* segment t1 - t2 */
                # plotCubicBezierSeg(x0,y0, x0+fx1,y0+fy1, x0+fx2,y0+fy2, x3,y3)
                for plot in ZinglPlotter.plot_cubic_bezier_seg(
                    x0, y0, x0 + fx1, y0 + fy1, x0 + fx2, y0 + fy2, x3, y3
                ):
                    yield plot
            x0 = x3
            y0 = y3
            fx0 = fx3
            fy0 = fy3
            t1 = t2
