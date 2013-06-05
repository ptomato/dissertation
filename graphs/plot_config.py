import os
import warnings

# Suppress warning about subsetting font in PDF file
warnings.filterwarnings('ignore', '.*can not be subsetted into a Type 3 font.*')

# Use a custom font manager in order to import our local fonts
if 'TTFPATH' not in os.environ:
    os.environ['TTFPATH'] = '../fonts;../../fonts'
from matplotlib import font_manager as _fm
_fm.fontManager = _fm.FontManager()

textwidth = 4.0  # inches; 101.6 mm
marginparwidth = 1.41  # inches; 36 mm
pagewidth = 5.57  # inches; 141.6 mm

import matplotlib as _m
import matplotlib.axes
import matplotlib.figure
import numpy as np
import tango

# Matplotlib configuration common to all plots in the thesis

_m.rc('font', **{
    'family': 'serif',
    'serif': 'Minion Pro',
    'sans-serif': 'Cantarell, URWClassico, URWClassico-Reg, Optima',
    'cursive': 'Lucida Handwriting',
    'size': 8})
_m.rc('mathtext', fontset='custom')
_m.rc('axes', color_cycle=tango.tango_color_cycle)
_m.rc('image',
    cmap='bone_r',
    origin='lower')
_m.rc('figure',
    figsize=(textwidth, 2.5),
    dpi=150)
_m.rc('lines',
    linewidth=1.0,
    markeredgewidth=1.0,
    markersize=3,
    color='black')
_m.rc('savefig', dpi=300)
_m.rc('path', simplify=True)
_m.rc('pdf', compression=9)


def phase_intensity_plot(self, phase, intensity, *args, **kwargs):
    """Plot 2-D phase and intensity arrays in the same axes; the intensity is the
    luminance, and the phase is the color"""

    if phase.ndim != 2 or intensity.ndim != 2:
        raise TypeError('The arrays must be 2-dimensional')

    hsv = np.ones(intensity.shape + (3,)) * 0.5
    hsv[..., 0] = phase / (2 * np.pi)
    hsv[..., 2] = intensity / intensity.max()
    rgb = _m.colors.hsv_to_rgb(hsv)

    self.imshow(rgb, *args, **kwargs)

    # Create a fake ScalarMappable so that the color bar comes out properly
    mappable = _m.image.AxesImage(self, norm=_m.colors.Normalize(),
        cmap=_m.cm.hsv)
    mappable.set_array(phase)
    return mappable


def field_plot(self, data, *args, **kwargs):
    """Make a phase-intensity plot of a 2-D complex array"""
    phase = np.angle(data) + np.pi
    intensity = np.abs(data) ** 2
    return self.phase_intensity_plot(phase, intensity, *args, **kwargs)


def subfigure_label(self, label, pos='upper left', **kwargs):
    """Make a label in a corner @pos of axes"""
    x = 0.1 if 'left' in pos else 0.9
    y = 0.9 if 'upper' in pos else 0.1
    self.text(x, y, label,
        transform=self.transAxes,
        horizontalalignment='center',
        verticalalignment='center',
        **kwargs)


def scale_bar(self, x, y, text, length=0.1, fontdict={}, **kwargs):
    """Make a scale bar"""
    scale_bar = _m.patches.Rectangle((x, y), length, 0.01,
        fill=True, transform=self.transAxes, **kwargs)
    self.add_patch(scale_bar)
    self.text(x + length / 2, y + 0.02, text,
        horizontalalignment='center', verticalalignment='bottom',
        transform=self.transAxes,
        fontdict=fontdict,
        **kwargs)


def nice_colorbar(self, mappable, fraction=0.05, ax=None, **kwargs):
    # Get the axes' size
    if ax is None:
        ax = self.gca()

    try:
        cax = ax.cax
    except AttributeError:
        x, y, x1, y1 = ax.get_position().get_points().flatten()
        width, height = x1 - x, y1 - y
        cax = self.add_axes([x + (1 - fraction) * width, y, fraction * width, height])

    return self.colorbar(mappable, ax=ax, cax=cax,
        format=_m.ticker.NullFormatter(),
        **kwargs)

# Monkeypatch matplotlib class
matplotlib.axes.Axes.phase_intensity_plot = phase_intensity_plot
matplotlib.axes.Axes.field_plot = field_plot
matplotlib.axes.Axes.subfigure_label = subfigure_label
matplotlib.axes.Axes.scale_bar = scale_bar
matplotlib.figure.Figure.nice_colorbar = nice_colorbar


class AbsNorm(_m.colors.Normalize):
    """A normalizer that makes sure that 0 is in the center of the color scale"""
    def __init__(self, limit=None, clip=False):
        try:
            _m.colors.Normalize.__init__(self, -limit, limit, clip)
        except TypeError:
            _m.colors.Normalize.__init__(self, None, None, clip)

    def autoscale(self, A):
        limit = abs(A.max())
        self.vmin = -limit
        self.vmax = limit

    def autoscale_None(self, A):
        if self.vmin is None or self.vmax is None:
            self.autoscale(A)
