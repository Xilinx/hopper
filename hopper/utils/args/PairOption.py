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

# Marked named value options (e.g. './app -t:data=value' or './app --test:data=value')
class PairOption(Option):
	def __init__(self, shortname, longname, description = None, keyname = None,
			multiple = False, required = False, valueoptional = False,
			default = {}, validoperators = None):
		Option.__init__(self, shortname, longname,
				description = description,
				multiple = multiple,
				required = required,
				default = {},
				validoperators = validoperators)
		self.valueoptional = valueoptional
		self.keyname = keyname

	def __matchesName__(self, name, longarg = False):
		nameSplit = name.split(":")
		for n in (self.longnames if longarg else self.shortnames):
			if nameSplit[0] == n:
				if len(nameSplit) == 1:
					warning("Argument '%s' is missing it's key." % name)
					return False
				return True
		return False

	def __addMatch__(self, instance, key, value):
		instance.getAsType(list).append((key, value[0], value[1]))

	def match(self, instance, arg, position = None):
		matched = self.__matchesOption__(instance, arg, not(self.valueoptional), True)
		if matched[0]:
			if matched[1] and matched[2] != None:
				nameSplit = matched[2].split(":")
				self.__addMatch__(instance, nameSplit[1], matched[3])
			return True
		return False
