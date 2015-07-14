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

import os, sys
import urllib2

from hopper.utils.logger import *

class TaskBase:
	def __init__(self, environment):
		self.environment = environment

	def execute(self, handler = None):
		if self.environment:
			if not self.environment.prepare():
				return False
		return True

class Environment:
	def __init__(self, basepath = os.getcwd(),
				logger = None, mirrorpath = None, proxy = None,
				threads = None, locallayers = None):
		self.workingPath = basepath
		self.threadlimit = threads
		self.mirrorpath = os.path.expanduser(mirrorpath) if mirrorpath else None
		self.proxy = proxy
		self.locallayers = locallayers
		self.logger = logger

		self.allowbuildtools = True

	def getMirrorPath(self):
		return self.mirrorpath

	def getSourceMirror(self):
		if not self.getMirrorPath():
			return None
		return os.path.join(self.getMirrorPath(), "repo-mirror")

	def getDownloadMirror(self):
		if not self.getMirrorPath():
			return None
		return os.path.join(self.getMirrorPath(), "downloads-mirror")

	def getDownloadMirrorUri(self):
		if not self.getDownloadMirror():
			return None
		return "file://" + self.getDownloadMirror()

	def getLocalLayerPath(self):
		return self.locallayers

	def getWorkingPath(self):
		return self.workingPath

	def getWorkingBuildPath(self):
		return os.path.join(self.getWorkingPath(), "build")

	def getWorkingTmpPath(self):
		return os.path.join(self.getWorkingBuildPath(), "tmp")

	def getWorkingDownloadPath(self):
		return os.path.join(self.getWorkingBuildPath(), "downloads")

	def getWorkingToolsPath(self):
		return os.path.join(self.getWorkingBuildPath(), "tools")

	def getWorkingSourcesPath(self):
		return os.path.join(self.getWorkingPath(), "repos")

	def getMaxThreads(self):
		return self.threadlimit

	def getProxy(self):
		return self.proxy

	def prepare(self):
		if not(os.path.exists(self.getWorkingPath())):
			self.note("Preparing environment at '%s'" % self.getWorkingPath())
			os.makedirs(self.getWorkingPath())

		if not(os.path.exists(self.getWorkingSourcesPath())):
			self.debug("    * create repo directory")
			os.makedirs(self.getWorkingSourcesPath())

		if not(os.path.exists(self.getWorkingBuildPath())):
			self.debug("    * create build directory")
			os.makedirs(self.getWorkingBuildPath())

		if not(os.path.exists(self.getWorkingTmpPath())):
			self.debug("    * create working tmp directory")
			os.makedirs(self.getWorkingTmpPath())

		return True

	def downloadFile(self, url):
		filename = url.split("/")[-1]

		# create downloads directory
		if not(os.path.exists(self.getWorkingDownloadPath())):
			os.makedirs(self.getWorkingDownloadPath())

		mirrorpath = None
		if self.getDownloadMirror():
			mirrorpath = os.path.join(self.getDownloadMirror(), filename)
		localpath = os.path.join(self.getWorkingDownloadPath(), filename)
		if os.path.isfile(localpath):
			return localpath
		elif mirrorpath and os.path.isfile(mirrorpath):
			import shutil
			shutil.copyfile(mirrorpath, localpath)
			return localpath
		else:
			try:
				result = Environment.__download__(url, localpath)
				if result:
					return localpath
			except urllib2.HTTPError as e:
				self.error(e)
				self.error("Failed to download file '%s'" % url)
		return None

	# Pass-through logging calls
	def getLogger(self):
		if self.logger:
			return self.logger
		return getDefaultLogger()

	def log(self, message, level = LoggerLevel.Normal, severity = LoggerSeverity.Info):
		self.getLogger().log(message, level, severity)

	def verbose(self, message):
		self.getLogger().verbose(message)

	def debug(self, message):
		self.getLogger().debug(message)

	def fdebug(self, message):
		self.getLogger().fdebug(message)

	def error(self, message):
		self.getLogger().error(message)

	def warning(self, message):
		self.getLogger().warning(message)

	def note(self, message):
		self.getLogger().note(message)

	@staticmethod
	def __download__(url, filepath):
		resp = urllib2.urlopen(url)
		size = int(resp.info()["Content-Length"])

		with open(filepath, "wb") as f:
			while True:
				data = resp.read(8192)
				if not data:
					break
				f.write(data)

		return resp

