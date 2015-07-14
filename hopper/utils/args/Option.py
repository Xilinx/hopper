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

from hopper.utils.logger import *

from BaseField import *
from hopper.utils.Collections import *

# Marked options (e.g. './app -t' or './app --test')
class Option(BaseField):
	def __init__(self, shortname, longname, description = None,
				multiple = False, required = False, default = None,
				validoperators = None):
		BaseField.__init__(self, description, multiple, required, default)
		self.shortnames = []
		self.longnames = []

		self.shortnames = getAsListOrIterable(shortname)
		self.longnames = getAsListOrIterable(longname)

		self.validoperators = validoperators

	def __matchesName__(self, name, longarg = False):
		for n in (self.longnames if longarg else self.shortnames):
			if name == n:
				return True
		return False

	def __matchesOption__(self, instance, arg, valueRequirement = False, valueAllowed = False):
		if arg[0] == '-' or arg[0:2] == '--':
			matched = False

			longarg = True if (arg[0:2] == '--') else False
			# Seperate the '-' from the value of the arg
			if longarg:
				valuearg = arg[2:]
			else:
				valuearg = arg[1:]

			# Split the arg into fields
			fields = None
			operator = "="
			if self.validoperators:
				for i in self.validoperators:
					if i in valuearg:
						operator = i
						break

			# split at operators
			fields = valuearg.split(operator, 1)

			if fields:
				# Check if the name matches this option
				nameMatches = self.__matchesName__(fields[0], longarg)

				if nameMatches:
					if len(fields) > 1 and not(valueAllowed):
						warning("Argument '%s' has value, but value is not expected." % arg)
						return (False, False, None, None)
					elif len(fields) == 1 and valueRequirement:
						warning("Argument '%s' is missing value, but value is expected." % arg)
						return (False, False, None, None)

					# Check multiple requirements
					if (not(instance.empty()) and self.multiple) or instance.empty():
						if len(fields) > 1:
							strippedvalue = fields[1].strip("'\"")
							return (True, True, fields[0], (operator, strippedvalue))
						else:
							return (True, True, fields[0], None)
					elif (not(instance.empty()) and not(self.multiple)):
						warning("Invalid Argument: Only a single '%s' option can be provided" % arg)
						return (True, False, None, None)
		return (False, False, None, None)

	def match(self, instance, arg, position = None):
		matches = self.__matchesOption__(instance, arg, False, False)
		if matches[0]:
			return True
		return False

	def __repr__(self):
		reprString = "CommandOption:"

		names = []
		for shortname in self.shortnames:
			names.append("-%s" % shortname)
		for longname in self.longnames:
			names.append("--%s" % longname)

		if len(names) != 0:
			reprString += " names = [ %s ]" % ", ".join(names)

		options = []
		if self.multiple:
			options.append("multiple")
		if self.required:
			options.append("required")

		if len(options) != 0:
			reprString += " (%s)" % ", ".join(options)

		return reprString
