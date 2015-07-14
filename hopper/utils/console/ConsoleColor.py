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
import TtyHelper

class ConsoleColor:
	ANSICodeStart = "\x1b["
	ANSICodeResetFormat = "0m"
	ANSICodeColourForeground = "3%dm"
	Black = 0
	Red = 1
	Green = 2
	Yellow = 3
	Blue = 4
	Magenta = 5
	Cyan = 6
	White = 7

	def __init__(self, color):
		self.color = color

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		pass

def colorString(string, color, forcecolor = False):
	if forcecolor or sys.stdout.isatty():
		newString = ConsoleColor.ANSICodeStart
		newString += ConsoleColor.ANSICodeColourForeground % color
		newString += str(string)
		newString += ConsoleColor.ANSICodeStart + ConsoleColor.ANSICodeResetFormat
		return newString
	else:
		return string

def getStdOutTextWidth():
	if sys.stdout.isatty():
		sz = TtyHelper.getTTYSize()
		if sz[0] > 80 or sz[0] < 0:
			return 80
		return sz[0]
	else:
		return 80
