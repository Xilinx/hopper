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
import hopper.utils.git.tasks

def getUriRepositoryName(uri):
	url = urlparse.urlparse(uri)
	clonename = url.path.strip("/").split("/")[-1]
	if clonename.endswith(".git"):
		clonename = clonename[0:len(clonename) - len(".git")]
	return clonename

class Repository:
	class ChangedState:
		Unchanged = 0
		Modified = 1
		Added = 2
		Deleted = 3
		Renamed = 4
		Copied = 5
		Updated = 6
		Untracked = 7
		Ignored = 8

		@staticmethod
		def parseStateFromGit(string):
			char = string.lower()
			if char == "m":
				return Repository.ChangedState.Modified
			elif char == "a":
				return Repository.ChangedState.Added
			elif char == "d":
				return Repository.ChangedState.Deleted
			elif char == "r":
				return Repository.ChangedState.Renamed
			elif char == "c":
				return Repository.ChangedState.Copied
			elif char == "u":
				return Repository.ChangedState.Updated
			elif char == "?":
				return Repository.ChangedState.Untracked
			elif char == "!":
				return Repository.ChangedState.Ignored
			return Repository.ChangedState.Unchanged

	def __init__(self, environment, path):
		self.environment = environment
		self.path = path

	def getPath(self):
		return self.path

	def __git__(self, command):
		return hopper.utils.git.tasks.GitTask.run(command, path = self.path, environment = self.environment)

	def valid(self):
		if os.path.exists(self.path) and os.path.isdir(self.path):
			if os.path.exists(os.path.join(self.path, ".git")):
				return True
			else:
				result = self.__git__(["rev-parse"])
				if result[0] == 0:
					return True
		return False

	def dirty(self, untracked = True):
		status = self.getStatus()
		if status:
			if len(status[0]) != 0 or len(status[1]) != 0:
				return True
			if untracked and len(status[2]) != 0:
				return True
		return False

	def remoteUpdate(self, remote = None):
		if remote:
			result = self.__git__(["remote", "update", remote])
		else:
			result = self.__git__(["remote", "update"])
		if result[0] == 0:
			return True
		return False

	def clone(self, remote, mirror = False, bare = False, overwrite = False):
		reference = hopper.utils.git.tasks.GitTask.getReference(remote, self.environment)

		args = ["clone"]
		if bare and not mirror:
			args.append("--bare")
		if mirror:
			args.append("--mirror")
		if reference:
			args.append("--no-hardlinks")
			args.append("--reference")
			args.append(reference)

		args.append(remote)
		args.append(self.path)

		if os.path.exists(self.path):
			if overwrite:
				if os.path.isfile(self.path) or os.path.islink(self.path):
					os.remove(self.path)
				else:
					shutil.rmtree(self.path)
			else:
				raise Exception("Repository or content already exists")

		result = self.__git__(args)
		if result[0] == 0:
			return True
		raise Exception("Clone failed - Exited %d, Output = %s" % (result[0], result[1]))

	def checkout(self, ref):
		if ref:
			result = self.__git__(["checkout", ref])
			if result[0] == 0:
				return True
		return False

	def describe(self, ref = None):
		if ref:
			result = self.__git__(["describe", "--dirty", "--all", "--exact-match", "--long", ref])
		else:
			result = self.__git__(["describe", "--dirty", "--all", "--exact-match", "--long"])
		if result[0] == 0:
			return result[1].splitlines()[0]
		return None

	def getTreeRef(self):
		result = self.__git__(["rev-parse", "HEAD", "--symbolic-full-name", "HEAD"])
		if result[0] == 0:
			lines = result[1].splitlines()
			sha = lines[0]
			ref = lines[1]
			if ref == "HEAD":
				ref = None
			return (ref, sha)
		return None

	def getStatus(self):
		result = self.__git__(["status", "--porcelain"])
		if result[0] == 0:
			index = {}
			working = {}
			untracked = []
			if result[1] and len(result[1]) != 0:
				for i in result[1].splitlines():
					istate = Repository.ChangedState.parseStateFromGit(i[0])
					wstate = Repository.ChangedState.parseStateFromGit(i[1])
					filename = i[3:]

					if istate == Repository.ChangedState.Untracked or wstate == Repository.ChangedState.Untracked:
						untracked.append(filename)
					if istate != Repository.ChangedState.Unchanged:
						index[filename] = istate
					if wstate != Repository.ChangedState.Unchanged:
						working[filename] = wstate
			return (index, working, untracked)
		return None

	def findRef(self, ref, remotename = None):
		if ref:
			fullref = None
			if remotename:
				result = self.__git__(["show-ref", "refs/remotes/%s/%s" % (remotename, ref)])
				if result[0] == 0 and len(result[1]) != 0:
					firstentry = result[1].splitlines()[0]
					if len(firstentry) != 0:
						fullref = firstentry.split()[1]

				if fullref:
					# find a local ref that tracks this ref
					fullrefcommit = self.getRefCommit(fullref)
					result = self.__git__(["for-each-ref", "--format=%(refname) %(upstream)", "refs/heads"])
					if result[0] == 0:
						for i in result[1].splitlines():
							parts = i.split()
							if parts[1] == fullref:
								return (parts[0], None, fullrefcommit)
					return (fullref, None, fullrefcommit)

			# local refs (and tags)
			result = self.__git__(["rev-parse", "--symbolic-full-name", ref])
			if result[0] == 0 and len(result[1]) != 0:
				firstref = result[1].splitlines()[0]
				if len(firstref) != 0:
					return (firstref, None, self.getRefCommit(firstref))

			# ref is a commit sha
			sha = self.absoluteSHA(ref)
			if sha:
				return (None, sha, sha)
		return None

	def shortRef(self, ref):
		if ref:
			result = self.__git__(["rev-parse", "--abbrev-ref", ref])
			if result[0] == 0 and len(result[1]) != 0:
				firstentry = result[1].splitlines()[0]
				return firstentry
		return None

	def absoluteSHA(self, sha):
		if sha:
			result = self.__git__(["rev-parse", sha])
			if result[0] == 0 and len(result[1]) != 0:
				firstentry = result[1].splitlines()[0]
				return firstentry
		return None

	def getRefs(self):
		result = self.__git__(["show-ref"])
		if result[0] == 0:
			refs = []
			for i in result[1].splitlines():
				parts = i.split()
				refs.append(parts[1])
			return refs
		return None

	def getRefCommit(self, ref):
		result = self.__git__(["show-ref", ref])
		if result[0] == 0:
			for i in result[1].splitlines():
				parts = i.split()
				return parts[0]
		return None

	def getCommitInfo(self, sha):
		result = self.__git__(["log", "-1", "--format=\"%H%n%an%n%ae%n%at%n%cn%n%ce%n%ct%n%s%n%b\"", sha])
		if result[0] == 0:
			data = result[1].splitlines()
			dictdata = {}
			dictdata["hash"] = data[0]
			dictdata["author.name"] = data[1]
			dictdata["author.email"] = data[2]
			dictdata["author.date"] = data[3]
			dictdata["committer.name"] = data[4]
			dictdata["committer.email"] = data[5]
			dictdata["commiter.date"] = data[6]
			dictdata["message"] = "\n".join(data[7:])
			return dictdata
		return None

	def getCommits(self, start, end = None):
		if end:
			self.environment.log("commit hash diff")
			result = self.__git__(["log", "--format=\"%H\"", start + "..." + end])
		else:
			self.environment.log("commit single list")
			result = self.__git__(["log", "--format=\"%H\"", start])

		self.environment.log("result[0] = %s" % (result[0]))
		self.environment.log("result[1] = %s" % (result[1]))
		if result[0] == 0:
			return result[1].splitlines()
		return None

	def getRemotes(self):
		result = self.__git__(["remote", "-v"])
		if result[0] == 0:
			remotes = {}
			for i in result[1].splitlines():
				parts = i.split()
				if parts[0] not in remotes:
					remotes[parts[0]] = parts[1]
			return remotes
		return None
