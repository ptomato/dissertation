import sys
sys.path.append('..')
import os
import subprocess
import itertools
import numpy as N
from enthought.mayavi import mlab
from tango import Tango
from simulation import SlitSystem

# Tango color palette
tango = Tango(return_format='float')


def rotations(iterable):
    """Generator that returns permutations of an iterable in order"""
    for n in range(len(iterable)):
        yield iterable[n:] + iterable[:n]

mlab.figure(1, bgcolor=tango.white, fgcolor=tango.black, size=(800, 800))
mlab.clf()

# Display a semi-transparent sphere
sphere = mlab.points3d(0, 0, 0,
    scale_mode='none',
    scale_factor=2,
    color=tango.aluminum3,
    resolution=50,
    opacity=0.7,
    name='Poincare')
sphere.actor.property.specular = 0.45
sphere.actor.property.specular_power = 5
sphere.actor.property.backface_culling = True

# Display Cartesian axes
mlab.points3d((0, 0), (0, 0), (0, 0), mode='axes', scale_factor=1.2)  # axes
mlab.quiver3d(*itertools.chain(rotations([1.2, 0, 0]), rotations([1, 0, 0])),
    color=tango.black,
    mode='arrow',
    scale_factor=0.1)  # axes arrows

# Display great circles
t = N.linspace(0, 2 * N.pi, 100, endpoint=True)
for coords in rotations([N.cos(t), N.sin(t), N.zeros_like(t)]):
    mlab.plot3d(*coords, tube_radius=None)

# Plotting parameters
plots = zip(
    ['D', 'A', 'R', 'L'],  # polarization
    [(0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)],  # incident stokes vector
    ['butter3', 'chameleon3', 'skyblue3', 'scarletred3'],  # colors
    [1, 1, 1, 1],  # E_TM
    [1, 1, 1, 1],  # E_TE
    [0, N.pi, N.pi / 2, -N.pi / 2],  # psi
)

# Simulation

b = N.arange(10, 830, 2) * 1e-9  # Slit width, 10-830 nm
calc = SlitSystem(b,
    wavelength=830e-9,               # Wavelength, 830 nm
    metal_epsilon=-29.321 + 2.051j,  # Relative permittivity, Au 830 nm (Palik)
    metal_thickness=200e-9,          # Film thickness, 200 nm
    incidence_index=1.00027487,
    slit_index=1.00027487,
    outcoupling_index=1.5102,
    collection_index=1.00027487,
    numerical_aperture=0.40,
    angle_of_incidence=0.0,
    C1=1.0, C2=1.0)

# Plot data
for pol, inf, color, E_TM, E_TE, psi in plots:
    s1, s2, s3, width = N.loadtxt('../../data/qwp/{0}-incidence.txt'.format(pol),
        skiprows=1,
        usecols=(2, 4, 6, 9),
        unpack=True)

    # Plot points
    mlab.points3d(s1, s2, s3, width, color=tango[color],
        resolution=12)
    mlab.points3d(inf[0], inf[1], inf[2], color=tango[color],
        mode='cube',
        scale_factor=0.2)  # coordinate of incident light

    # Plot smooth lines according to theory
    R = calc.T_TM / calc.T_TE
    norm = E_TE ** 2 + R * E_TM ** 2
    s1_theory = (E_TE ** 2 - R * E_TM ** 2) / norm
    s2_theory = 2 * N.sqrt(R) * E_TM * E_TE * N.cos(calc.dphase - psi) / norm
    s3_theory = -2 * N.sqrt(R) * E_TM * E_TE * N.sin(calc.dphase - psi) / norm

    mlab.plot3d(s1_theory, s2_theory, s3_theory,
        color=tango[color],
        tube_radius=0.005)

mlab.view(160, 75, 4.9, [0, .35, .25])
mlab.savefig('poincare.png')

if 'batch' not in sys.argv:
    mlab.show()

# Automatically update the PDF for our LaTeX file, using the new PNG
# subprocess.call([r'D:\Program Files\Inkscape\inkscape.exe',
#     '--without-gui',
#     '--export-pdf=poincare.pdf',
#     r'{0}\poincare.svg'.format(os.getcwd())])
