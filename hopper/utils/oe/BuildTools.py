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

import os
import platform
import urllib
from distutils.version import StrictVersion

import hopper.utils.tasks
import hopper.utils.process

class BuildToolsHelper:
	# These dependencies must be provided by the host
	sysRequiredDeps = [
			"gcc",
			"g++",
			]

	defaultYoctoVersion = StrictVersion("1.8")
	minimumKernel = StrictVersion("2.6.32")

	@staticmethod
	def determineHostCompatiblity():
		for i in BuildToolsHelper.sysRequiredDeps:
			if hopper.utils.process.ProcessHelper.searchPath(i):
				debug("has '%s'" % i)
			else:
				error("missing '%s'" % i)
				return False

		return True

	@staticmethod
	def getKernelVersion():
		if platform.system() == "Linux":
			return StrictVersion(platform.uname()[2].split("-")[0])
		return None

	@staticmethod
	def getBuildToolsTarballUrl():
		baseUri = "http://downloads.yoctoproject.org/releases/yocto/"
		linuxVersion = BuildToolsHelper.getKernelVersion()
		if linuxVersion:
			# default poky/yocto pre-builts (this version currently does not work)
			if linuxVersion >= BuildToolsHelper.minimumKernel:
				if platform.machine() == "x86_64":
					return baseUri + ("yocto-%s/buildtools/" % BuildToolsHelper.defaultYoctoVersion) + \
							"poky-glibc-x86_64-buildtools-tarball-core2-64-buildtools-nativesdk-standalone-%s.sh" % \
							BuildToolsHelper.defaultYoctoVersion

		return None

	@staticmethod
	def getSystemSysroot(buildtoolspath):
		types = ["pokysdk-linux", "oesdk-linux"]
		systemroot = os.path.join(buildtoolspath, "sysroots")

		for i in types:
			p = os.path.join(systemroot, "%s-%s" % (platform.machine(), i))
			if os.path.isdir(p):
				return p

		return None

# This task prepares and expands a buildtools tarball
class BuildToolsTask(hopper.utils.tasks.TaskBase):
	def __init__(self, environment):
		hopper.utils.tasks.TaskBase.__init__(self, environment)

	def execute(self, handler = None):
		if not hopper.utils.tasks.TaskBase.execute(self, handler):
			return False

		if not BuildToolsHelper.determineHostCompatiblity():
			raise Exception("Host is not compatible, resolve dependencies.")

		# find and expand the required tarball
		downloadUrl = BuildToolsHelper.getBuildToolsTarballUrl()
		if downloadUrl == None:
			raise Exception("Unable to find a valid build tools download for you system.")

		if os.path.isdir(self.environment.getWorkingToolsPath()) and \
				len(os.listdir(self.environment.getWorkingToolsPath())) != 0:
			self.environment.note("Build tools already populated, skipping install step")
			return True

		self.environment.log("Retrieving buildtools tarball")
		localpath = self.environment.downloadFile(downloadUrl)
		if localpath == None:
			raise Exception("Unable to retrieve buildtools tarball")

		# install it to the build/tools/ directory
		proc = hopper.utils.process.Process(self.environment,
				["sh", localpath, "-y", "-d", self.environment.getWorkingToolsPath()])
		self.environment.log("Installing buildtools in '%s'" % self.environment.getWorkingToolsPath())
		result = proc.execute()
		if result and result[0] != 0:
			raise Exception("Running buildtools install failed in '%s'" % self.environment.getWorkingToolsPath())

		return True

