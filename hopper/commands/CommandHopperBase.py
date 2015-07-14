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
import urlparse
from hopper.utils.logger import *
import hopper.utils.args
import hopper.utils.Proxy
import hopper.utils.tasks

class CommandHopperBase(hopper.utils.args.CommandBase):
	threadLimit = hopper.utils.args.ValueOption(
			None, "threads",
			default = None,
			description = "The maximum number of concurrent threads avaliable.\n" +
				"(Default is to automatically detect)")

	mirror = hopper.utils.args.ValueOption(
			None, "mirror",
			default = None,
			description = "The location of a git repository mirror. These repositories will be used to seed the clones.\n" +
				"(This can be defined via the environment variable HOPPER_MIRROR.)")

	locallayers = hopper.utils.args.ValueOption(
			None, "local-layers",
			default = None,
			description = "The location of layers for which are local and can be symlinked to. This is useful for development.\n" +
				"(This can be defined via the environment variable HOPPER_LOCAL.)")

	def __init__(self):
		hopper.utils.args.CommandBase.__init__(self)
		self.environment = None

	def execute(self, handler = None):
		hopper.utils.args.CommandBase.execute(self)

		if self.threadLimit:
			threads = self.threadLimit
		else:
			threads = CommandHopperBase.getDefaultThreads()

		self.environment = hopper.utils.tasks.Environment(
				basepath = os.getcwd(),
				mirrorpath = CommandHopperBase.valueOrEnvironment(self.mirror, "HOPPER_MIRROR"),
				proxy = CommandHopperBase.getProxy(),
				threads = threads,
				locallayers = CommandHopperBase.valueOrEnvironment(self.locallayers, "HOPPER_LOCAL"))

		return True

	@staticmethod
	def valueOrEnvironment(value, env):
		if value:
			return value
		elif env in os.environ:
			return os.environ[env]
		return None

	@staticmethod
	def getDefaultThreads():
		import multiprocessing
		systemthreads = multiprocessing.cpu_count()
		activecpus = systemthreads / 2
		debug("Detected %s threads avaliable to system (using half, %s threads)" % (systemthreads, activecpus))
		# Check if using LSF and account for it
		if "LSB_DJOB_NUMPROC" in os.environ:
			try:
				activecpus = int(os.environ["LSB_DJOB_NUMPROC"])
				warning("Forced default threads by LSF environment to %s threads" % activecpus)
			except:
				pass
		return activecpus

	@staticmethod
	def getHttpProxyUri():
		if "http_proxy" in os.environ:
			return urlparse.urlparse(os.environ["http_proxy"])
		elif "HTTP_PROXY" in os.environ:
			return urlparse.urlparse(os.environ["HTTP_PROXY"])
		return None

	@staticmethod
	def getProxy():
		uri = CommandHopperBase.getHttpProxyUri()
		if uri:
			return hopper.utils.Proxy.Proxy(uri.hostname, uri.port)
		return None

