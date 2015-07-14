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


class BaseFieldValue:
	def __init__(self, parent):
		self.value = None
		self.parent = parent

	def parse(self, arg, position = None):
		if self.parent:
			return self.parent.match(self, arg, position)
		return False

	def empty(self):
		if self.value:
			return False
		return True

	def get(self):
		return self.value

	def getAsType(self, expectedtype):
		if self.value:
			if type(self.value) != expectedtype:
				raise Exception("BaseFieldValue accessed, was type '%s' but expects '%s'" % (type(self.value), expectedtype))
			else:
				return self.value
		else:
			self.value = expectedtype()
			return self.value

	def getOrDefault(self, default = None):
		if self.value:
			return self.value
		else:
			if default:
				return default
			elif self.parent:
				return self.parent.default
		return None

	def set(self, value):
		self.value = value

	def __repr__(self):
		reprString = "BaseFieldValue: value = %s\n" % repr(self.value)
		return reprString

# Base Class to represent a command field (option or otherwise)
class BaseField:
	def __init__(self, description = None, multiple = False, required = False, default = None):
		self.default = default
		self.multiple = multiple
		self.required = required
		self.description = description

	def match(self, instance, arg, position = None):
		return False
