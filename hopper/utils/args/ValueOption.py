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

from Option import *
from hopper.utils.Collections import *

# Marked Value options (e.g. './app -t=value' or './app --test=value')
class ValueOption(Option):
	def __init__(self, shortname, longname, description = None,
				multiple = False, required = False, default = None):
		# Account for multiple and force the default to be a list or a fixed value
		if multiple:
			expecteddefault = getAsListOrIterable(default)
		else:
			expecteddefault = default

		Option.__init__(self, shortname, longname, description,
				multiple, required, default = expecteddefault)

	def match(self, instance, arg, position = None):
		matches = self.__matchesOption__(instance, arg, True, True)
		if matches[0]:
			if matches[1]:
				if matches[3]:
					value = matches[3][1]
					if self.multiple:
						instance.getAsType(list).append(value)
					else:
						instance.set(value)
			return True
		return False

