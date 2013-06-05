import numpy as N
"""
Crystal plane geometry, of a set of planes equal by symmetry: magnitude_factor
is the mangnitude of the lattice vector in units of 1/a, where a is the lattice
constant; multiplicity is the number of planes in the first Brillouin zone;
label is the {xyz} Miller index for the set of planes.
"""


class CrystalPlane:
    def __init__(self, x, y, z):
        b1 = N.array([-1, 1, 1])
        b2 = N.array([1, -1, 1])
        b3 = N.array([1, 1, -1])
        self.magnitude_factor = N.sqrt(((x * b1 + y * b2 + z * b3) ** 2).sum())
        self.multiplicity = 48 / max([x, y, z])
        self.label = '{{{}{}{}}}'.format(int(x), int(y), int(z))

if __name__ == '__main__':
    p111 = CrystalPlane(1, 1, 1)
    assert p111.magnitude_factor == N.sqrt(3)
    assert p111.multiplicity == 48
    assert p111.label == '{111}'

    p200 = CrystalPlane(2, 0, 0)
    assert p200.magnitude_factor == 2 * N.sqrt(3)
    assert p200.multiplicity == 24
    assert p200.label == '{200}'
