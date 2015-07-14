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

import os

from hopper.utils.logger import *

import hopper.commands.CommandBake
import hopper.utils.args
import hopper.utils.console.TtyHelper
import hopper.utils.git.repo
from hopper.utils.console.ConsoleColor import ConsoleColor, colorString

def getHopperInfomation(debugmode = False):
	gitinfo = hopper.utils.git.repo.Repository(None, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
	if gitinfo.valid():
		description = gitinfo.describe()
		return "hopper (version: %s)\n" % colorString(description, ConsoleColor.Green)
	return "hopper (not in git)\n"

def waitForChildPids():
	while True:
		try:
			os.waitpid(0, 0)
		except OSError:
			break
		except KeyboardInterrupt:
			pass

def setupLogger():
	logger = hopper.utils.logger.CodeFilteredLogger(verbosity = LoggerLevel.Verbose)
	if os.getenv("DEBUG") == "all":
		logger.level = LoggerLevel.Debug

	logger.setInverse(True)
	logger.addPackageFilter("hopper.utils.args") # filter out all debug from args parsing
	logger.addPackageFilter("hopper.utils.git") # filter out all debug from git execution
	logger.addPackageFilter("hopper.utils.process") # filter out all debug from process execution
	setDefaultLogger(logger)

def main(args):
	with hopper.utils.console.TtyHelper.TtyState():
		setupLogger()
		print(getHopperInfomation(False))
		command = None
		try:
			parser = hopper.utils.args.CommandHandler()
			parser.setDefault(hopper.commands.CommandBake.CommandBake)
			parser.addCommand(hopper.utils.args.CommandHelp)
			parser.addCommand(hopper.commands.CommandBake.CommandBake)
			command = parser.getCommand(args)
			if command and command.execute(parser):
				return 0
		except hopper.utils.args.ArgumentParserException as e:
			error(e.message)
		except KeyboardInterrupt:
			warning("Attempted to terminate, waiting on bitbake to clean up.")
			waitForChildPids()
		return -1
