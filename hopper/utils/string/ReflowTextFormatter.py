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


def is_wrapping_character(char):
	if char == ',' or char == '.' or char == ':' or char == ';' or char == '?' or char == '!':
		return True
	return False

def is_newline_character(char):
	if char == '\r' or char == '\n':
		return True
	return False

def is_spacing_character(char):
	if char == ' ' or char == '\t':
		return True
	return False

class ReflowTextFormatter:
	def __init__(self, width, prefix = "", suffix = ""):
		self.width = width
		self.prefix = prefix
		self.suffix = suffix

		self.reset()

	def reset(self):
		self.formattedData = self.prefix
		self.currentlen = 0

	def __reflow_insert__(self, block, transition):
		# Check if the block will wrap to a newline
		if self.currentlen + len(transition) + len(block) + len(self.prefix) + len(self.suffix) >= self.width:
			self.currentlen = len(block);
			self.formattedData += self.suffix + "\n" + self.prefix + block
		else:
			self.currentlen += len(transition) + len(block);
			self.formattedData += transition + block

	def __reflow_insert_new__(self):
		self.formattedData += self.suffix + "\n" + self.prefix
		self.currentlen = 0;

	def reflow(self, content):
		current = ""
		transition = ""
		for i in content:
			if is_wrapping_character(i):
				current = current + i
				self.__reflow_insert__(current, transition)
				current = ""
				transition = ""
			elif is_newline_character(i):
				# if the character is a new-line then insert a new line
				self.__reflow_insert__(current, transition)
				current = ""
				transition = ""
				self.__reflow_insert_new__()
			elif is_spacing_character(i):
				if not(len(current) == 0):
					self.__reflow_insert__(current, transition)
					current = ""
					transition = ""
				# add to the transition block 
				transition = transition + i
			else:
				# can't wrap here, add to the block
				current = current + i

		if not(len(current) == 0):
			self.__reflow_insert__(current, transition)
			current = ""
			transition = ""

		return self.formattedData

def reflowFormatter(data, width = 80, prefix = "", suffix = ""):
	formatter = ReflowTextFormatter(width, prefix, suffix)
	return formatter.reflow(data) + "\n"
