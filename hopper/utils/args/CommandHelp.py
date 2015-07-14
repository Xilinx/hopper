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

from hopper.utils.logger import *
from hopper.utils.console.ConsoleColor import getStdOutTextWidth
from hopper.utils.string.ReflowTextFormatter import *

from hopper.utils.Collections import *

from CommandBase import *
from CommandHandler import *
from Parameter import *
from Option import *
from PairOption import *
from ValueOption import *
from BooleanOption import *
from RepositoryOption import *

class CommandHelp(CommandBase):
	CommandName = "help"

	helpTarget = Parameter("command", multiple = False, index = 0)

	def execute(self, handler = None):
		if not CommandBase.execute(self):
			return False

		if not self.helpTarget:
			targets = [ "help" ]
			printListing = True
		else:
			targets = self.helpTarget
			printListing = False

		self.defaultTextWidth = getStdOutTextWidth()

		command = handler.findCommandByName(getFirstIterable(targets))
		if command:
			commandNames = CommandHandler.getCommandNameFromClass(command)
			print("  %s [options] %s" % (commandNames[0], self.generateParameterLine(command)))
			if len(commandNames) > 1:
				print("    (aliases: %s)" % ", ".join(commandNames[1:]))

			print("")
			for i in CommandHandler.getAllFieldsFromClass(command).iteritems():
				if not isinstance(i[1], Parameter):
					print("%s" % self.generateOptionInfo(command, i[1]))
		else:
			error("Command '%s' does not exist." % getFirstIterable(self.helpTarget))
			printListing = True

		if printListing:
			print("")
			print("Valid commands:")
			for i in handler.commands:
				print("    %s" % ", ".join(CommandHandler.getCommandNameFromClass(i)))

		print("")
		return True

	def generateParameterLine(self, command):
		orderedParams = []
		params = []
		for i in CommandHandler.getAllFieldsFromClass(command).iteritems():
			if isinstance(i[1], Parameter):
				if i[1].index != -1:
					orderedParams.append(i)
				else:
					params.append(i)

		paramStrings = []

		for i in orderedParams:
			while (i[1].index + 1) > len(paramStrings):
				paramStrings.append(None)
			if i[1].multiple:
				paramStrings[i[1].index] = "%s..." % i[1].name
			else:
				paramStrings[i[1].index] = "%s" % i[1].name

		for i in params:
			if i[1].multiple:
				paramStrings.append("%s..." % i[1].name)
			else:
				paramStrings.append("%s" % i[1].name)


		return " ".join(paramStrings)

	def generateOptionInfo(self, command, option):
		info = "    "
		if isinstance(option, Option):
			argnames = []
			additionalpart = ""
			if isinstance(option, PairOption):
				additionalpart = ":<%s>" % option.keyname
				valuepart = "<value>"
				if isinstance(option, RepositoryOption):
					valuepart = "<version>[@<remote/path>]"

				if option.valueoptional:
					additionalpart += "[=%s]" % valuepart
				else:
					additionalpart += valuepart
			elif isinstance(option, ValueOption):
				additionalpart = "=<value>"

			for i in option.shortnames:
				argnames.append("-%s%s" % (i, additionalpart))
			for i in option.longnames:
				argnames.append("--%s%s" % (i, additionalpart))

			hasargs = False
			currentargsinfo = ""
			for i in range(0, len(argnames)):
				additional = argnames[i]
				if i + 1 != len(argnames):
					additional += ","
				if len(currentargsinfo) + len(additional) >= self.defaultTextWidth:
					info += currentargsinfo + "\n    "
					currentargsinfo = ""
				currentargsinfo += additional
			if currentargsinfo != "":
				info += currentargsinfo + "\n"
				currentargsinfo = ""

			if option.description:
				info += reflowFormatter(option.description, self.defaultTextWidth,
						prefix = "        ")
		return info
