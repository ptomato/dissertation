"""Tango color palette"""

class Tango:
	"""
	Tango color palette.

	(see http://tango.freedesktop.org/Tango_Icon_Theme_Guidelines)

	Get any Tango color as an attribute or index of this class. White and black
	are also included for convenience. 'aluminum' is an alias for 'aluminium'.

	>>> tango = Tango()
	>>> tango.white
	'#ffffff'
	>>> tango.black
	'#000000'
	>>> tango.skyblue3
	'#204a87'
	>>> tango.aluminium5
	'#555753'
	>>> tango.aluminum6
	'#2e3436'
	>>> tango.unknown
	Traceback (most recent call last):
		...
	AttributeError: "unknown" is not in the Tango palette
	>>> tango.scarletred4
	Traceback (most recent call last):
		...
	AttributeError: "scarletred4" is not in the Tango palette
	>>> tango = Tango(return_format='float')
	>>> tango.chameleon3
	(0.3058823529411765, 0.6039215686274509, 0.023529411764705882)
	>>> tango = Tango(return_format='unknown')
	>>> tango.chameleon3
	Traceback (most recent call last):
		...
	ValueError: "unknown" is not a valid return format
	"""

	_palette = {
	    'butter': (
			(0xfc, 0xe9, 0x4f),
			(0xed, 0xd4, 0),
			(0xc4, 0xa0, 0)),
		'orange': (
			(0xfc, 0xaf, 0x3e),
			(0xf5, 0x79, 0),
			(0xce, 0x5c, 0)),
		'chocolate': (
			(0xe9, 0xb9, 0x6e),
			(0xc1, 0x7d, 0x11),
			(0x8f, 0x59, 0x02)),
		'chameleon': (
			(0x8a, 0xe2, 0x34),
			(0x73, 0xd2, 0x16),
			(0x4e, 0x9a, 0x06)),
		'skyblue': (
			(0x72, 0x9f, 0xcf),
			(0x34, 0x65, 0xa4),
			(0x20, 0x4a, 0x87)),
		'plum': (
			(0xad, 0x7f, 0xa8),
			(0x75, 0x50, 0x7b),
			(0x5c, 0x35, 0x66)),
		'scarletred': (
			(0xef, 0x29, 0x29),
			(0xcc, 0, 0),
			(0xa4, 0, 0)),
		'aluminium': (
			(0xee, 0xee, 0xec),
			(0xd3, 0xd7, 0xcf),
			(0xba, 0xbd, 0xb6),
			(0x88, 0x8a, 0x85),
			(0x55, 0x57, 0x53),
			(0x2e, 0x34, 0x36))
	}
	_formats = {
		'hex': lambda p: '#{0[0]:02x}{0[1]:02x}{0[2]:02x}'.format(p),
		'float': lambda p: (p[0] / 255.0, p[1] / 255.0, p[2] / 255.0)
	}

	def __init__(self, return_format='hex'):
		"""
		@return_format: Format in which to return the colors. Allowed values:
			'hex': web-style hex triplets ("#204a87")
			'float': 3-tuples of floats between 0 and 1
		"""
		self._return_format = return_format

	def __getattr__(self, name):
		if name == 'white':
			return self._formats[self._return_format]((0xff, 0xff, 0xff))
		if name == 'black':
			return self._formats[self._return_format]((0, 0, 0))
		if name == 'aluminum':
			return getattr(self, 'aluminium')
		if name[-1] in '123456' and name[:-1] in ('aluminium', 'aluminum'):
			return getattr(self, 'aluminium')[int(name[-1]) - 1]
		if name[-1] in '123' and name[-2] not in '123':
			return getattr(self, name[:-1])[int(name[-1]) - 1]
		if name in self._palette.keys():
			try:
				return map(self._formats[self._return_format], self._palette[name])
			except KeyError:
				raise ValueError('"{0}" is not a valid return format'.format(self._return_format))
		else:
			raise AttributeError('"{0}" is not in the Tango palette'.format(name))

	def __getitem__(self, name):
		return getattr(self, name)

tango = Tango()
"""
Instance of the Tango class with 'hex' return format

Provided for convenience; just do
	from tango import tango
"""

tango_color_cycle = (tango.skyblue3, tango.scarletred3, tango.chameleon3,
	tango.orange3, tango.plum3, tango.butter3, tango.black)
"""
Color cycle appropriate for Matplotlib's RC parameter axes.color_cycle.
"""

if __name__ == '__main__':
	import doctest
	doctest.testmod()
