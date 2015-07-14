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

from hopper.utils.logger import *

class LocalSource:
	def __init__(self, name, path = None):
		self.name = name
		self.path = path

	def canFetch(self):
		return True

	def getPath(self, environment):
		if self.path:
			return self.path
		if self.name:
			for local in [environment.getLocalLayerPath()]:
				if local and os.path.exists(local):
					valid = [self.name, self.name + ".git"]
					for i in os.listdir(local):
						if i in valid:
							return os.path.join(local, i)
		return None

	def __repr__(self):
		return "LocalSource (%s@%s)" % (self.name, self.path)

class GitSource:
	def __init__(self, remote, ref):
		self.remote = remote
		self.ref = ref

	def canFetch(self):
		if self.remote != None:
			return True
		return False

	def getPath(self, environment):
		if self.remote:
			return os.path.join(environment.getWorkingSourcesPath(),
					GitSource.getUriCloneName(self.remote))
		return None

	def __repr__(self):
		return "GitSource (%s@%s)" % (self.ref, self.remote)

	@staticmethod
	def getUriCloneName(uri):
		url = urlparse.urlparse(uri)
		clonename = url.path.strip("/").split("/")[-1]
		if clonename.endswith(".git"):
			clonename = clonename[0:len(clonename) - len(".git")]
		return clonename

class Layer:
	def __init__(self, name, path = None, source = None):
		self.name = name
		self.path = path
		self.source = source

	def getName(self):
		return self.name

	def getFullName(self):
		if self.path:
			return self.name + "/" + self.path
		return self.name

	def getPath(self):
		return self.path

	def getSourcePath(self, environment):
		if self.source:
			sourceroot = self.getRootSourcePath(environment)
			if self.path:
				sourceroot = os.path.join(sourceroot, self.path)
			return sourceroot
		return None

	def getRootSourcePath(self, environment):
		if self.source:
			return self.source.getPath(environment)
		return None

	def isBitBake(self):
		if self.getName() == "bitbake":
			return True
		return False

	def __repr__(self):
		return "Meta '%s' {%s} (source = %s)" % (self.name, self.path, self.source)

# Handles parsing and filling in data about layers and repos
class LayerCollection:
	def __init__(self, defaultversion = None):
		self.indexes = []
		self.layers = []

		self.defaultversion = GitSource(None, defaultversion)

	def __iter__(self):
		return self.layers.__iter__()

	def __len__(self):
		return len(self.layers)

	def addIndex(self, index):
		self.indexes.append(index)

	# validates that the layers and bitbake is available
	def validate(self, warnonly = False):
		hasBitbake = False
		for i in self.layers:
			if i.isBitBake():
				hasBitbake = True
				break

		if not hasBitbake:
			if warnonly:
				warning("BitBake is missing from the described layers.")
			else:
				warning("BitBake is missing from the described layers, adding BitBake.")
				bblayer = self.__findlayer__(
						LayerCollection.getLayerNameTriple("bitbake", False),
						GitSource(None, "master"))
				if bblayer:
					self.layers.append(bblayer)
				else:
					error("Could not find BitBake")
					return False

		# TODO: check dependencies

		return True

	# Will parse a input set of repos and layers in the args form and result in a list
	def parse(self, layers):
		for l in layers.iteritems():
			names = LayerCollection.getLayerNameTriple(l[0], False)
			revision = LayerCollection.parseRevisionInfo(names[0],
					l[1]["path"], l[1]["ref"],
					self.defaultversion.ref)

			clayer = self.__findlayer__(names, revision)
			if clayer:
				self.layers.append(clayer)

	def add(self, name, version = None):
		names = LayerCollection.getLayerNameTriple(name, False)
		revision = version or self.defaultversion

		layer = self.__findlayer__(names, revision)
		if layer:
			if layer not in self.layers:
				self.layers.append(layer)
			return layer
		return None

	def __findlayer__(self, names, revision = None):
		layer = None
		# check the collection first
		if self.layers:
			for i in self.layers:
				if i.getName() == names[1]:
					return i

		subpath = names[2] or ""
		if revision != None and revision.canFetch():
			# enough info to create the layer
			layer = Layer(names[1], subpath, revision)
		else:
			# find layer in index and or create
			# TODO: refactor into a "serachLayerUri" function
			layerinfo = self.search(names[1])
			if layerinfo:
				fullrevision = revision
				if fullrevision == None:
					fullrevision = GitSource(layerinfo["remote"], None)
				elif isinstance(fullrevision, GitSource):
					fullrevision = GitSource(layerinfo["remote"], fullrevision.ref)
				else:
					warning("Unable to fill in source information for layer '%s'." % names[1])
					raise Exception("Unable to fill in source information for layer '%s'." % names[1])

				if "subpath" in layerinfo:
					subpath = layerinfo["subpath"]

				layer = Layer(names[1], subpath, fullrevision)
			else:
				warning("Unable to fill in source information for layer '%s'." % names[1])
				raise Exception("Unable to fill in source information for layer '%s'." % names[1])

		return layer

	def search(self, name):
		# search the index for a layer with the same name and repo (if specified
		for i in self.indexes:
			found = i.find(name)
			if found:
				return found
		return None

	def hash(layers):
		import hashlib
		hashstrings = []
		for i in layers:
			fullname = i.getFullName()
			revstring = ""
			if isinstance(i.source, GitSource):
				revstring = "%s@%s" % (i.source.ref, i.source.remote)
			m = hashlib.md5()
			m.update(fullname)
			m.update(revstring)
			hashstrings.append((fullname, m.hexdigest()))

		# sort the strings according to fullname order
		m = hashlib.md5()
		for i in sorted(hashstrings, key = lambda k : k[0]):
			m.update(i[1])
		return m.hexdigest()[0:16]

	@staticmethod
	def parseRevisionInfo(name, remote, ref, defaultref = None):
		if ref == "local" and name != None:
			# Symbolic Local Source
			return LocalSource(name, remote)

		if (ref != None and len(ref) != 0):
			# assumes git repo
			return GitSource(remote, ref)

		if defaultref:
			return GitSource(remote, defaultref)

		return None

	@staticmethod
	def getLayerNameTriple(name, repospecifier = False):
		repo = None
		path = None
		layer = None

		if repospecifier:
			reponame = name
		else:
			nameparts = name.split("/")
			repo = nameparts[0]
			layer = nameparts[-1]
			path = "/".join(nameparts[1:])
			if len(path) <= 0:
				path = None
		return (repo, layer, path)

