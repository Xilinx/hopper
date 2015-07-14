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
import urlparse
import shutil

from hopper.utils.logger import *
import hopper.utils.process
import hopper.utils.Proxy

class GitTask(hopper.utils.process.Process):
	@staticmethod
	def run(command, path = None, environment = None):
		process = GitTask(environment, command, path)
		return process.execute()

	def __init__(self, environment, command, path = None):
		hopper.utils.process.Process.__init__(self, environment, command)
		self.repopath = path

	def getArgs(self):
		rebuilt = []
		rebuilt.append("git")

		gitdir = self.repopath
		worktree = None

		# if not a bare repo, setup worktree
		if gitdir and os.path.exists(gitdir):
			if os.path.exists(os.path.join(gitdir, ".git")):
				worktree = gitdir
				gitdir = os.path.join(gitdir, ".git")

		if gitdir:
			rebuilt += ["--git-dir", gitdir]
		if worktree:
			rebuilt += ["--work-tree", worktree]

		# Proxy overrides
		if self.environment:
			proxy = self.environment.getProxy()
			if proxy:
				rebuilt.append("-c")
				rebuilt.append("http.proxy=%s" % proxy.getHttpURI())
				self.environment.debug("GitTask: using http proxy '%s'" % proxy.getHttpURI())

				rebuilt.append("-c")
				if hopper.utils.Proxy.Proxy.getProxyTunnelCommand():
					rebuilt.append("core.gitproxy=%s" % hopper.utils.Proxy.Proxy.getProxyTunnelCommand())
				self.environment.debug("GitTask: using gitproxy '%s'" % hopper.utils.Proxy.Proxy.getProxyTunnelCommand())

		for i in self.command:
			rebuilt.append(i)
		return rebuilt

	@staticmethod
	def getReference(remote, environment = None):
		if environment:
			clonename = hopper.utils.git.repo.getUriRepositoryName(remote)
			reference = environment.getSourceMirror()
			referenceargs = []
			if reference != None:
				if os.path.exists(os.path.join(reference, clonename + ".git")):
					return os.path.join(reference, clonename + ".git")
				if os.path.exists(os.path.join(reference, clonename)):
					return os.path.join(reference, clonename)
		return None

