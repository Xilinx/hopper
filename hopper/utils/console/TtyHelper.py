# Copyright (c) 2015 Xilinx Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import os

def getTTYSize():
	def ioctl_GWINSZ(fd):
		try:
			import fcntl, termios, struct, os
			cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,'1234'))
		except:
			return None
		return cr
	cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
	if not cr:
		try:
			fd = os.open(os.ctermid(), os.O_RDONLY)
			cr = ioctl_GWINSZ(fd)
			os.close(fd)
		except:
			pass
	if not cr:
		try:
			cr = (env['LINES'], env['COLUMNS'])
		except:
			return None
	return int(cr[1]), int(cr[0])

def prompt(prefix, echo = True):
	import termios
	ttystate = None
	if sys.stdin.isatty() and not echo:
		ttystate = termios.tcgetattr(sys.stdin)
		ttynewstate = termios.tcgetattr(sys.stdin)
		ttynewstate[3] = ttynewstate[3] & ~termios.ECHO
		termios.tcsetattr(sys.stdin, termios.TCSADRAIN, ttynewstate)

	result = None
	try:
		result = raw_input(prefix)
		if not echo:
			sys.stdout.write('\n') # the non-echoed mode will not emit the newline
	except KeyboardInterrupt:
		pass

	if sys.stdin.isatty() and not echo:
		termios.tcsetattr(sys.stdin, termios.TCSADRAIN, ttystate)

	return result

class TtyState:
	def __init__(self):
		self.state = None

	def __enter__(self):
		self.store()
		return self

	def __exit__(self ,type, value, traceback):
		self.restore()

	def store(self):
		if sys.stdout.isatty():
			import hopper.utils.process
			result = hopper.utils.process.Process.run([ "stty", "-g" ])
			if result[0] == 0:
				self.state = result[1].strip()

	def restore(self):
		if sys.stdout.isatty() and self.state:
			import hopper.utils.process
			hopper.utils.process.Process.run([ "stty", self.state ])
