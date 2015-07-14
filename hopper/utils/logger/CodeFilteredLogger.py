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


from Logger import *

class CodeFilteredLogger(SimpleLogger):
	def __init__(self, verbosity = LoggerLevel.Normal, inverse = False):
		SimpleLogger.__init__(self, verbosity)

		self.filters = []
		self.inverse = inverse

	def addPackageFilter(self, package):
		self.filters.append((package, None, None))

	def addClassFilter(self, classname, package = None):
		self.filters.append((package, classname, None))

	def setInverse(self, inverse):
		self.inverse = inverse

	def __passsesFilter__(self, packagename, classname, functionname):
		for i in self.filters:
			if i[0] != None and packagename == i[0]:
				if i[1] != None and classname == i[1]:
					if i[2] != None and functionname == i[2]:
						return True
					elif i[2] == None:
						return True
				elif i[1] == None:
					if i[2] != None and functionname == i[2]:
						return True
					elif i[2] == None:
						return True
			elif i[0] == None:
				if i[1] != None and classname == i[1]:
					if i[2] != None and functionname == i[2]:
						return True
					elif i[2] == None:
						return True
				elif i[1] == None:
					if i[2] != None and functionname == i[2]:
						return True
					elif i[2] == None:
						return True
		return False

	def passesFilter(self, packagename, classname, functionname):
		passes = self.__passsesFilter__(packagename, classname, functionname)
		if self.inverse:
			return not(passes)
		return passes

	def __getCaller__(self):
		import inspect
		stack = inspect.stack()

		firstFrame = None
		# escape Logger to a non-logger frame
		for i in stack:
			g = i[0].f_globals
			if "__package__" in g:
				if g["__package__"] != __package__:
					firstFrame = i[0]
					break
		if "__package__" in firstFrame.f_globals:
			packageName = firstFrame.f_globals["__package__"]
		else:
			packageName = None
		functionName = inspect.getframeinfo(firstFrame)[2]
		selfObject = firstFrame.f_locals.get('self', None)
		if selfObject != None:
			className = selfObject.__class__.__name__
		else:
			className = None

		return (packageName, className, functionName)

	def log(self, message, level = LoggerLevel.Normal, severity = LoggerSeverity.Info):
		if severity == LoggerSeverity.Debug:
			caller = self.__getCaller__()

			#print("Location = ")
			#print("    package = '%s'" % caller[0])
			#print("    class = '%s'" % caller[1])
			#print("    function = '%s'" % caller[2])
			if self.passesFilter(caller[0], caller[1], caller[2]):
				SimpleLogger.log(self, message, level, severity)
		else:
			SimpleLogger.log(self, message, level, severity)
