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
import urlparse
import shutil

import hopper.utils.tasks
import meta
import hopper.utils.git.repo

class LayerFetchGitTask(hopper.utils.tasks.TaskBase):
	def __init__(self, environment, revision, forceupdate = False):
		hopper.utils.tasks.TaskBase.__init__(self, environment)

		self.revision = revision
		self.forceupdate = forceupdate

	def __repr__(self):
		if self.revision:
			clonename = hopper.utils.git.repo.getUriRepositoryName(self.revision.remote)
			return "Git Fetch '%s' @ %s" % (clonename, self.revision.ref)
		return "Invalid Git Fetch"

	def execute(self, handler = None):
		if not self.revision and not isinstance(self.revision, meta.GitSource):
			return False

		clonename = hopper.utils.git.repo.getUriRepositoryName(self.revision.remote)
		path = os.path.join(self.environment.getWorkingSourcesPath(), clonename)
		remoteuri = self.revision.remote
		gitrepo = hopper.utils.git.repo.Repository(self.environment, path)

		# Need to clone repo
		justcloned = False
		if not gitrepo.valid():
			self.environment.verbose("%s: Cloning..." % (clonename))
			if not gitrepo.clone(remoteuri, overwrite = True):
				raise Exception("Failed to clone '%s' from '%s'" % (clonename, remoteuri))
			justcloned = True

		# check for the remotes, dont assume its valid
		remotes = gitrepo.getRemotes()
		self.environment.debug("%s: remotes -> '%s'" % (clonename, remotes))
		remotename = None
		for i in remotes.iteritems():
			if i[1] == remoteuri:
				remotename = i[0]
				break
		self.environment.debug("%s: remotename = '%s'" % (clonename, remotename))

		if self.forceupdate and not justcloned:
			if not gitrepo.remoteUpdate(remotename):
				raise Exception("Failed to fetch/update '%s'" % (clonename))

		# determine the absolute ref/commit
		ref = gitrepo.findRef(self.revision.ref, remotename)

		# Ensure repo is checked out to the correct ref/commit
		dirty = gitrepo.dirty()
		head = gitrepo.getTreeRef()

		validcheckout = False
		if ref and head:
			if (head[0] == None and ref[0] == None) or (head[0] == ref[0]):
				if (head[1] == None and ref[1] == None or ref[1] == None) or (head[1] == ref[1]):
					self.environment.log("%s: Already checked out at expected ref" % (clonename))
					validcheckout = True

		if not validcheckout:
			self.environment.log("%s: Not checked out to a valid ref/commit" % (clonename))
			if ref[0] != None:
				objcheckout = gitrepo.shortRef(ref[0])
				if ref[0].startswith("refs/remote"):
					# create the local branch using the name of the ref specified
					objcheckout = self.revision.ref
			elif ref[1] != None:
				objcheckout = ref[1]
			else:
				raise Exception("No ref/commit to checkout '%s'" % repr(ref))

			if dirty:
				raise Exception("Cannot checkout '%s' due to dirty state" % (clonename))

			self.environment.log("%s: Checking out '%s'" % (clonename, objcheckout))
			if not gitrepo.checkout(objcheckout):
				raise Exception("Failed to checkout '%s' for '%s'" % (objcheckout, clonename))

			# TODO: figure out how to update local ref
			#if not gitrepo.pull():

		# determine the ref after updating/adding a local branch
		ref = gitrepo.findRef(self.revision.ref, remotename)
		dirty = gitrepo.dirty()
		head = gitrepo.getTreeRef()

		# repo info
		info = "%s:\n" % (clonename)
		info += "  * head     = %s\n" % (repr(head))
		info += "  * expected = %s -> sha = %s\n" % (repr((ref[0], ref[1])), ref[2])
		info += "  * path = %s\n" % path
		info += "  * '%s' = %s\n" % (remotename, remoteuri)
		self.environment.log(info)

		# return the path to the cloned repo
		return path

def generateLayerFetchTasks(environment, collection, forceupdate = False):
	tasks = []

	if collection:
		# find all remotes and revisions
		# TODO: fix so that the magic string is the name of the repo/layer
		srcs = {}
		for i in collection:
			if isinstance(i.source, meta.GitSource):
				clonename = hopper.utils.git.repo.getUriRepositoryName(i.source.remote)
				if clonename not in srcs:
					srcs[clonename] = (i.source, [i.getName()])
				else:
					# already in the list, check if the revision is matching
					current = srcs[clonename]
					if current[0].ref != i.source.ref:
						# TODO: handle this case
						environment.error("Mis-matched sources between layers (%s and %s)" % (current[1], i.getName()))
						raise Exception("Mis-matched sources between layers (%s and %s)" % (current[1], i.getName()))
					else:
						srcs[clonename][1].append(i.getName())
			elif isinstance(i.source, meta.LocalSource):
				if i.source.name not in srcs:
					srcs[i.source.name] = (i.source, [i.source.name])
				else:
					# already in list, check mis-match
					raise Exception("TODO")

		for i in srcs.iteritems():
			if isinstance(i[1][0], meta.GitSource):
				task = LayerFetchGitTask(environment, i[1][0], forceupdate)
				tasks.append(task)
			elif isinstance(i[1][0], meta.LocalSource):
				pass

	return tasks

