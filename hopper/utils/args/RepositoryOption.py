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

from PairOption import *

class RepositoryOption(PairOption):
	def __init__(self, shortname, longname, description = None,
				keyname = None, multiple = False, required = False,
				valueoptional = False, repospecifier = False):
		PairOption.__init__(self, shortname, longname,
				description = description,
				keyname = keyname,
				multiple = multiple,
				required = required,
				valueoptional = valueoptional,
				default = {})
		self.repospecifier = repospecifier

	def __parseSpecifier__(self, key, value):
		path = None
		revision = None # Default version value
		commitid = None

		if value:
			localsplit = value[1].split("@")
			refsplit = localsplit[0].split(":")
			revision = localsplit[0]

			if len(localsplit) >= 2:
				path = localsplit[1]

			if len(refsplit) >= 2:
				revision = refsplit[0]
				commitid = refsplit[1]

			if revision and len(revision) == 0:
				revision = None

		returnvalue = {}
		returnvalue["name"] = key
		returnvalue["repo"] = self.repospecifier
		returnvalue["ref"] = revision
		returnvalue["commit"] = commitid
		returnvalue["path"] = path
		return returnvalue

	def __addMatch__(self, instance, key, value):
		instance.getAsType(dict)[key] = self.__parseSpecifier__(key, value)
