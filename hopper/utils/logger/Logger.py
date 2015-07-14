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
import datetime
import threading

class LoggerSeverity:
	Info= 0
	Error = 1
	Warning = 2
	Note = 3
	Debug = 4
	Unknown = 5

class LoggerLevel:
	All = -1
	HeavyDebug = 100000
	Debug = 10000
	FullVerbose = 1000
	Verbose = 100
	Normal = 10

class Logger:
	defaultlogger = None
	def __init__(self, verbosity = LoggerLevel.Normal):
		self.level = verbosity

	def log(self, message, level = LoggerLevel.Normal, severity = LoggerSeverity.Info):
		pass

	def verbose(self, message):
		self.log(message, LoggerLevel.Verbose, LoggerSeverity.Info)

	def debug(self, message):
		self.log(message, LoggerLevel.Debug, LoggerSeverity.Debug)

	def fdebug(self, message):
		self.log(message, LoggerLevel.HeavyDebug, LoggerSeverity.Debug)

	def error(self, message):
		self.log(message, LoggerLevel.Normal, LoggerSeverity.Error)

	def warning(self, message):
		self.log(message, LoggerLevel.Normal, LoggerSeverity.Warning)

	def note(self, message):
		self.log(message, LoggerLevel.Verbose, LoggerSeverity.Note)

class SimpleLogger(Logger):
	defaultlogger = None
	stdoutputlock = threading.RLock()

	def __init__(self, verbosity = LoggerLevel.Normal):
		Logger.__init__(self, verbosity)
		self.enableprefix = True
		self.timestamp = False

	def log(self, message, level = LoggerLevel.Normal, severity = LoggerSeverity.Info):
		from hopper.utils.console.ConsoleColor import ConsoleColor, colorString
		with SimpleLogger.stdoutputlock:
			splitup = str(message).splitlines()
			for i in splitup:
				if level <= self.level or self.level == LoggerLevel.All:
					prefix = ""
					if self.enableprefix:
						if severity == LoggerSeverity.Info:
							prefix = colorString("INFO:  ", ConsoleColor.Blue)
						elif severity == LoggerSeverity.Error:
							prefix = colorString("ERROR: ", ConsoleColor.Red)
						elif severity == LoggerSeverity.Warning:
							prefix = colorString("WARN:  ", ConsoleColor.Yellow)
						elif severity == LoggerSeverity.Note:
							prefix = colorString("NOTE:  ", ConsoleColor.White)
						elif severity == LoggerSeverity.Debug:
							prefix = colorString("DEBUG: ", ConsoleColor.Cyan)
					if self.timestamp:
						prefix = "(%s) " % datetime.datetime.now().strftime("%X") + prefix
					print("%s%s" % (prefix, i))
					sys.stdout.flush()

class FileLogger(Logger):
	def __init__(self, filepath, verbosity = LoggerLevel.Normal):
		Logger.__init__(self, verbosity)
		self.enableprefix = False
		self.timestamp = False
		self.filestream = open(filepath, "w")
		self.writelock = threading.RLock()

	def close(self):
		self.filestream.close()

	def log(self, message, level = LoggerLevel.Normal, severity = LoggerSeverity.Info):
		with self.writelock:
			splitup = str(message).splitlines()
			for i in splitup:
				if level <= self.level or self.level == LoggerLevel.All:
					prefix = ""
					if self.enableprefix:
						if severity == LoggerSeverity.Info:
							prefix = "INFO:  "
						elif severity == LoggerSeverity.Error:
							prefix = "ERROR: "
						elif severity == LoggerSeverity.Warning:
							prefix = "WARN:  "
						elif severity == LoggerSeverity.Note:
							prefix = "NOTE:  "
						elif severity == LoggerSeverity.Debug:
							prefix = "DEBUG: "
					if self.timestamp:
						prefix = "(%s) " % datetime.datetime.now().strftime("%X") + prefix
					self.filestream.write("%s%s\n" % (prefix, i))
					self.filestream.flush()

class PrefixPassLogger(Logger):
	def __init__(self, logger, prefix = None):
		Logger.__init__(self)
		self.logger = logger
		self.prefix = prefix

	def log(self, message, level = LoggerLevel.Normal, severity = LoggerSeverity.Info):
		if self.logger:
			splitup = str(message).splitlines()
			for i in splitup:
				if self.prefix:
					self.logger.log("%s: %s" % (self.prefix, i), level, severity)
				else:
					self.logger.log(i, level, severity)

class MassLogger(Logger):
	def __init__(self):
		Logger.__init__(self)
		self.loggers = []
		self.loggerslock = threading.RLock()

	def addLogger(self, logger, key = None):
		with self.loggerslock:
			self.loggers.append((logger, key))

	def getLogger(self, key):
		with self.loggerslock:
			for i in self.loggers:
				if i[1] == key:
					return i[0]
		return None

	def log(self, message, level = LoggerLevel.Normal, severity = LoggerSeverity.Info):
		with self.loggerslock:
			if len(self.loggers) != 0:
				splitup = str(message).splitlines()
				for i in splitup:
					for l in self.loggers:
						l[0].log(i, level, severity)

