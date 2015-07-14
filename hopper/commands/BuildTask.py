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

from hopper.utils.bitbake.BitBakeTask import *
import hopper.utils.bitbake.mirrors
import hopper.utils.bitbake.config

import hopper.source.fetcher

import hopper.utils.tasks
from hopper.utils.oe.BuildTools import *

import shutil

class BuildTask(hopper.utils.tasks.TaskBase):
	def __init__(self, environment, config):
		hopper.utils.tasks.TaskBase.__init__(self, environment)

		self.tasks = []

		# config to build (layers, environment, confs)
		self.config = config

		# Targets
		self.targets = []

		# Log file
		self.outputlogger = None

		self.subshell = False
		self.updateMirror = False
		self.overwriteconfig = True

	def execute(self, handler = None):
		if not hopper.utils.tasks.TaskBase.execute(self, handler):
			return False

		self.tasks.append(BuildToolsTask(self.environment))
		self.tasks += hopper.source.fetcher.generateLayerFetchTasks(self.environment, self.config.layers)

		# execute tasks
		for i in self.tasks:
			i.execute(handler)

		# Build
		result = self.__build__()
		if result:
			if result[1]:
				for i in result[1].warnings:
					self.environment.warning("Build: %s" % i)
				for i in result[1].errors:
					self.environment.error("Build: %s" % i)

			if result[0] != 0:
				return result

		if self.updateMirror and self.environment.getDownloadMirror():
			if not hopper.utils.bitbake.mirrors.SourceMirror.updateMirror(self.environment,
					self.environment.getDownloadMirror()):
				raise Exception("Failed to update download mirror")

		return result

	def __build__(self):
		if self.subshell:
			self.environment.log("Preparing subshell")
			if "SHELL" in os.environ:
				shellargs = os.environ["SHELL"].split()
				step = BitBakeTask(self.environment, self.config, shellargs)
			else:
				step = BitBakeTask(self.environment, self.config, ["bash"])
		else:
			self.environment.log("Starting Bitbake for the following targets (machine = %s):" % self.config.machine)
			step = BitBakeTask.taskBuild(self.environment, self.config, self.targets)

		if len(self.targets) != 0:
			self.environment.log("    * targets = %s" % ",".join(self.targets))

		step.overwrite = self.overwriteconfig
		step.sublogger = self.outputlogger

		return step.execute()

