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

import collections

from BaseField import *
from hopper.utils.Collections import *

# Non-marked parameters/arguments. (e.g. './app file')
# Names are not required for parameters to function.
class Parameter(BaseField):
	def __init__(self, name, description = None, multiple = False,
			required = False, index = -1, default = None):
		BaseField.__init__(self, description, multiple, required, getAsListOrIterable(default))
		self.name = name
		self.index = index

	def __matchesParameter__(self, instance, arg, position):
		if arg[0] == '-' or arg[0:2] == '--':
			return False
		else:
			if (not(self.multiple) and instance.empty()) or (self.multiple):
				if self.index == -1:
					return True
				elif position != None:
					if not(self.multiple) and (position == self.index):
						return True
					elif self.multiple and (position >= self.index):
						return True
		return False

	def match(self, instance, arg, position = None):
		if self.__matchesParameter__(instance, arg, position):
			if self.multiple:
				instance.getAsType(list).append(arg)
			else:
				instance.set(arg)
			return True
		return False

	def __repr__(self):
		options = []
		if self.multiple:
			options.append("multiple")
		if self.required:
			options.append("required")
		if self.index != -1:
			options.append("parameter @ %d" % self.index)

		if len(options) != 0:
			return "CommandParameter: name = '%s' (%s)" \
					% (self.name, ", ".join(options))
		return "CommandParameter: name = '%s'" % (self.name)
