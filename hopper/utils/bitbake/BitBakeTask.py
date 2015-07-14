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
import os
import shutil
import subprocess
import re
import threading

from hopper.utils.logger import *
import hopper.utils.bitbake.config
import hopper.utils.process

class BitBakeResult:
	TaskUnknown = 0
	TaskRunning = 1
	TaskComplete = 2
	TaskFailed = 3

	@staticmethod
	def __parsestate__(state):
		s = state.lower()
		if s == "started":
			return BitBakeResult.TaskRunning
		elif s == "succeeded":
			return BitBakeResult.TaskComplete
		elif s == "failed":
			return BitBakeResult.TaskFailed
		return BitBakeResult.TaskUnknown

	def __init__(self):
		self.warnings = []
		self.errors = []
		self.tasks = []

	def updatetask(self, recipe, name, state):
		# find it in the collection
		for i in self.tasks:
			if i[0] == recipe and i[1] == name:
				i[2] = state
				return

		# create it
		newstate = [recipe, name, state]
		self.tasks.append(newstate)

class BitBakeKnottyListener(hopper.utils.process.ProcessListener):
	def __init__(self, logger):
		self.lock = threading.RLock()
		self.logger = logger
		self.state = BitBakeResult()

	def result(self):
		with self.lock:
			return self.state

	def __updateresult__(self, line):
		with self.lock:
			m = re.search("(NOTE|WARNING|ERROR): (.*)", line)
			if m:
				if m.group(1) == "WARNING":
					self.state.warnings.append(m.group(2))
				elif m.group(1) == "ERROR":
					self.state.errors.append(m.group(2))
				elif m.group(1) == "NOTE":
					mtask = re.search("recipe (.*?): task (.*?): (.*)", m.group(2))
					if mtask:
						self.state.updatetask(mtask.group(1), mtask.group(2),
								BitBakeResult.__parsestate__(mtask.group(3)))

	def update(self, data, err = False):
		for i in data.splitlines():
			if self.logger != None:
				self.logger.log(i)

			self.__updateresult__(i)

class BitBakeTask(hopper.utils.process.Process):
	def __init__(self, environment, config, command = []):
		hopper.utils.process.Process.__init__(self, environment, command)
		self.redirect = False
		self.workingDirectory = self.environment.getWorkingPath()

		self.config = config
		self.bbenvironment = {}
		self.overwrite = True
		self.sublogger = None

	@staticmethod
	def convertTargetArgs(targets, striptask = False):
		if targets:
			tasklist = []
			taskcount = 0
			for i in targets:
				if ":" in i and not(striptask):
					tasklist.append(i.split(":"))
					taskcount += 1
				else:
					tasklist.append((i, None))

			if (len(tasklist) > 1 and taskcount != 0) or taskcount > 1:
				raise Exception("BitBake and Hopper does not implement mixed task building, only one task with one target.")

			args = []
			for i in tasklist:
				if i[0] != None and len(i[0]) != 0:
					if i[1] != None and len(i[1]) != 0:
						args.append("-c")
						args.append(i[1])
					args.append(i[0])
			return args
		return []

	@staticmethod
	def taskBuild(environment, config, targets):
		return BitBakeTask(environment, config,
			["bitbake", "-k"] + BitBakeTask.convertTargetArgs(targets))

	def execute(self):
		self.environment.log("Starting bitbake process '%s'" % " ".join(self.command))
		if not self.config:
			raise Exception("BitBake Configuration is missing from the task.")

		self.environment.log("Prepare BitBake Configuration")
		configgen = hopper.utils.bitbake.config.ConfigurationGenerator(self.environment, self.config)
		if not configgen.generate(overwrite = self.overwrite):
			raise Exception("Failed to generate configuration")

		if self.sublogger:
			self.redirect = True
			listener = BitBakeKnottyListener(self.sublogger)
			result = hopper.utils.process.Process.execute(self, listeners = [listener])
			return (result[0], listener.result())

		result = hopper.utils.process.Process.execute(self)
		return (result[0], None)

	def getEnvironment(self):
		env = hopper.utils.process.Process.getEnvironment(self)

		scriptdirs = []
		bitbakedir = None
		for i in self.config.layers:
			sourcepath = i.getSourcePath(self.environment)
			rootsourcepath = i.getRootSourcePath(self.environment)

			# find bitbake
			if i.isBitBake():
				bitbakedir = sourcepath
			elif i.getName() == "poky":
				bitbakedir = os.path.join(sourcepath, "bitbake")

			# any layers and roots of layers with scripts directories
			for p in [sourcepath, rootsourcepath]:
				path = os.path.join(p, "scripts")
				if path and os.path.isdir(path):
					if path not in scriptdirs:
						self.environment.verbose("Adding scripts directory '%s' to path (from layer '%s')" % (path, i.getName()))
						scriptdirs.append(path)

		self.environment.debug("Preparing bitbake environment")
		env["BUILDDIR"] = self.environment.getWorkingPath()

		if scriptdirs:
			for i in scriptdirs:
				if os.path.exists(i):
					env["PATH"] += ":%s" % i

		if bitbakedir and os.path.exists(bitbakedir):
			env["BITBAKEDIR"] = bitbakedir
			env["PATH"] += ":%s/bin" % bitbakedir
		else:
			raise Exception("BitBake is required, not found in repo/layers")

		# Sanitize PATH
		oldpath = env["PATH"]
		if oldpath.find("\r") >= 0 or oldpath.find("\n") >= 0:
			warn("Your environment PATH variable contains '\\r' and/or '\\n' characters (consider cleaning that up)")
			oldpath = oldpath.replace('\r', '').replace('\n', '')
		newpath = []
		for i in oldpath.split(":"):
			if i and len(i) > 0:
				newpath.append(i)
		env["PATH"] = ":".join(newpath)
		self.environment.debug("env[PATH] = '%s'" % env["PATH"])

		# Whitelist some passthrough variables
		envWhitelist = ["HTTP_PROXY", "http_proxy",
				"HTTPS_PROXY", "https_proxy",
				"FTP_PROXY", "ftp_proxy",
				"FTPS_PROXY", "ftps_proxy",
				"NO_PROXY", "no_proxy",
				"ALL_PROXY", "all_proxy",
				"SSH_AGENT_PID", "SSH_AUTH_SOCK",
				"GIT_SSL_CAINFO", "GIT_SSL_CAPATH",
				]

		self.environment.debug("Preparing bitbake environment overrides")
		for i in self.bbenvironment.iteritems():
			self.environment.debug("env['%s'] = '%s'" % (i[0], i[1]))
			env[i[0]] = i[1]
			envWhitelist.append(i[0])

		env["BB_ENV_EXTRAWHITE"] = " ".join(envWhitelist)
		self.environment.debug("BB_ENV_EXTRAWHITE = '%s'" % env['BB_ENV_EXTRAWHITE'])

		return env

