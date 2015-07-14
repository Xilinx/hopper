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

from hopper.utils.logger import *
from hopper.utils.Collections import *

from ArgumentParserException import *
from CommandBase import *
from BaseField import *

class CommandHandler:
	def __init__(self):
		self.commands = []
		self.default = None

	@staticmethod
	def getCommandNameFromClass(c):
		if c:
			attrs = dir(c)
			if "CommandName" in attrs:
				return getAsListOrIterable(getattr(c, "CommandName"))
		return None

	@staticmethod
	def getAllFieldsFromClass(c):
		if c:
			fields = {}
			for attrname in dir(c):
				if not attrname.startswith("__"):
					attr = getattr(c, attrname)
					if not callable(attr) and isinstance(attr, BaseField):
						fields[attrname] = attr
			return fields
		return None

	def getCommand(self, args):
		command = None
		options = list()
		fields = list()

		# Find the Command
		for i in args[1:]:
			if i.startswith("-"):
				options.append(i)
			else:
				# assume first arg is the command otherwise there is no command
				if not(command) and len(fields) == 0:
					command = self.findCommandByName(i)
					if not(command):
						fields.append(i)
				else:
					fields.append(i)

		if command == None:
			if self.default:
				command = self.default
			else:
				raise ArgumentParserException("No command specified, and no default fallback avaliable.")

		# Associated fields for the command
		commandFields = {}
		debug("Command: '%s' -> fields:" % (command))
		if command:
			for i in CommandHandler.getAllFieldsFromClass(command).iteritems():
				commandFields[i[0]] = BaseFieldValue(i[1])
				debug("    * '%s' -> %s" % (i[0], i[1]))

		# Match all options first
		for i in options:
			matched = False
			for f in commandFields.iteritems():
				#debug("Testing option '%s' against '%s'" % (i, f))
				if f[1].parse(i):
					matched = True
					break
			if not(matched):
				raise ArgumentParserException("Unknown Argument '%s'" % i)

		# Match all fields
		fieldindex = 0
		for i in fields:
			matched = False
			for f in commandFields.iteritems():
				#debug("Testing field '%s' against '%s'" % (i, f))
				if f[1].parse(i, fieldindex):
					matched = True
					break
			if not(matched):
				raise ArgumentParserException("Unknown Argument '%s'" % i)
			else:
				fieldindex += 1

		if command != None:
			commandInstance = command()
			# Populate the command with its values
			debug("Parsed fields:")
			for i in commandFields.iteritems():
				debug("    * '%s' -> %s" % (i[0], i[1]))
				commandInstance.__dict__[i[0]] = i[1].getOrDefault()

			commandInstance.__options__()
			debug(repr(commandInstance))
			debug(repr(commandInstance.__dict__))

			if commandInstance != None:
				return commandInstance
		return None

	def findCommandByName(self, name):
		for i in self.commands:
			names = CommandHandler.getCommandNameFromClass(i)
			if names and name in names:
				return i
		return None

	def addCommand(self, command):
		if issubclass(command, CommandBase):
			self.commands.append(command)
		else:
			raise TypeError("Attempted to add '%s' as command which does not inherit from CommandBase" % command)

	def setDefault(self, command):
		if issubclass(command, CommandBase):
			self.default = command
		else:
			raise TypeError("Attempted to set '%s' as default command which does not inherit from CommandBase" % command)
