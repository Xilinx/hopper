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

import subprocess
import os, sys
import re
import fcntl
import threading

from hopper.utils.logger import *
import hopper.utils.tasks
import hopper.utils.oe.BuildTools

class ProcessHelper:
	@staticmethod
	def searchPath(filename):
		path = os.environ["PATH"]
		if path:
			for i in path.split(":"):
				fullpath = os.path.abspath(os.path.join(i, filename))
				if os.path.isfile(fullpath):
					if os.access(fullpath, os.X_OK):
						return fullpath
		return None

class ProcessBackgroundReaderThread(threading.Thread):
	def __init__(self, file, updatefn):
		threading.Thread.__init__(self)
		self.file = file
		self.updatefn = updatefn

	def run(self):
		if self.file:
			while not(self.file.closed):
				value = self.file.readline()
				if self.updatefn:
					self.updatefn(value, file)
				if value == "":
					break

class ProcessListener:
	def input(self, data, err = False):
		pass

class CulumativeListener(ProcessListener):
	def __init__(self, erroronly = False):
		self.lock = threading.RLock()
		self.output = ""
		self.erroronly = erroronly

	def result(self):
		with self.lock:
			return self.output

	def update(self, data, err = False):
		with self.lock:
			if (self.erroronly and err) or not self.erroronly:
				for i in data.splitlines():
					self.output += i + "\n"

class Process(hopper.utils.tasks.TaskBase):
	@staticmethod
	def run(command, environment = None):
		process = Process(environment, command)
		return process.execute()

	def __init__(self, environment, command):
		hopper.utils.tasks.TaskBase.__init__(self, environment)

		self.command = command
		self.redirect = True
		self.workingDirectory = None
		self.listeners = []

	def logger(self):
		if self.environment:
			return self.environment.getLogger()
		return getDefaultLogger()

	def getArgs(self):
		return self.command

	def getEnvironment(self):
		env = os.environ.copy()
		if self.environment:
			proxy = self.environment.getProxy()
			if proxy:
				# Setup the proxy settings in the environment
				env["http_proxy"] = proxy.getHttpURI()
				env["HTTP_PROXY"] = proxy.getHttpURI()
				env["https_proxy"] = proxy.getHttpsURI()
				env["HTTPS_PROXY"] = proxy.getHttpsURI()
				env["ftp_proxy"] = proxy.getFtpURI()
				env["FTP_PROXY"] = proxy.getFtpURI()

			# prepend the buildtools paths
			if self.environment.getWorkingToolsPath() != None and self.environment.allowbuildtools:
				sysroot = hopper.utils.oe.BuildTools.BuildToolsHelper.getSystemSysroot(
						self.environment.getWorkingToolsPath())
				self.logger().debug("build tools sysroot = %s" % sysroot)
				if sysroot != None:
					env["PATH"] = "%s/:" % os.path.join(sysroot, "bin") + env["PATH"]
					env["PATH"] = "%s/:" % os.path.join(sysroot, "usr/bin") + env["PATH"]
					env["PYTHONPATH"] = ""
					env["GIT_SSL_CAINFO"] = os.path.join(sysroot, "etc", "ssl", "certs", "ca-certificates.crt")
		return env

	def execute(self, handler = None, listeners = []):
		commandargs = self.getArgs()
		self.logger().debug("process: created '%s' (redirect = %s)" % (commandargs, self.redirect))
		p = subprocess.Popen(commandargs,
				stderr = subprocess.PIPE if self.redirect else None,
				stdout = subprocess.PIPE if self.redirect else None,
				cwd = self.workingDirectory,
				env = self.getEnvironment())

		# Setup listeners
		alllisteners = []
		if self.redirect:
			alllisteners += [CulumativeListener(False), CulumativeListener(True)]
		if listeners != None:
			alllisteners += listeners

		# Setup pipe threads
		def updateListener(data, file):
			for i in alllisteners:
				i.update(data, err = (file == p.stderr))

		if self.redirect:
			stdoutPipe = ProcessBackgroundReaderThread(p.stdout, updateListener)
			stderrPipe = ProcessBackgroundReaderThread(p.stderr, updateListener)
			stdoutPipe.start()
			stderrPipe.start()

		# Wait for process to exit
		p.wait()

		if self.redirect:
			stdoutPipe.join()
			stderrPipe.join()

		self.logger().debug("process: exec '%s' - result = %d" % (commandargs, p.returncode))
		if self.redirect and len(alllisteners) >= 2:
			return (p.returncode, alllisteners[0].result(), alllisteners[1].result())
		return (p.returncode, None, None)

