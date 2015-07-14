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
import datetime

from hopper.utils.logger import *
import hopper.utils.git.tasks
import hopper.utils.git.repo
import hopper.source.meta
import threading

class Watcher:
	class GroupState:
		def __init__(self, layers):
			self.layers = layers
			self.refstate = {}

		def getRefPairs(self):
			pairs = []
			for i in self.layers:
				if i.source and isinstance(i.source, hopper.source.meta.GitSource):
					if i.source.canFetch():
						# TODO: handle ref/tag/commit properly below
						pairs.append((i.source.remote, "refs/heads/" + i.source.ref))
			return pairs

		def filterPairs(self, remoterefs):
			filteredrefs = {}
			for p in self.getRefPairs():
				if p[0] in remoterefs:
					for i in remoterefs[p[0]].iteritems():
						if i[0] == p[1]:
							if p[0] not in filteredrefs:
								filteredrefs[p[0]] = {}
							filteredrefs[p[0]][i[0]] = i[1]
			return filteredrefs

		def update(self, remoterefs, trigger = False):
			rrefs = self.filterPairs(remoterefs)
			pairs = self.getRefPairs()

			changed = False
			oldrefstate = self.refstate
			newrefstate = {}
			for i in pairs:
				if i[0] in rrefs:
					if i[1] in rrefs[i[0]]:
						newcommit = rrefs[i[0]][i[1]]
						if i[0] not in newrefstate:
							newrefstate[i[0]] = {}
						newrefstate[i[0]][i[1]] = newcommit
						log("remote: %s, ref: %s, value = %s" % (i[0], i[1], newcommit))

						if trigger:
							changed = True
						if oldrefstate != None:
							if i[0] in oldrefstate and i[1] in oldrefstate[i[0]]:
								if newrefstate[i[0]][i[1]] != oldrefstate[i[0]][i[1]]:
									changed = True

			self.refstate = newrefstate
			return changed

		def cloneRefPin(self, remoterefs):
			filtered = self.filterPairs(remoterefs)

			# create layers that match the layers object, fill in pinned refs
			pinnedlayers = hopper.source.meta.LayerCollection(self.layers.defaultversion)
			for i in self.layers:
				if isinstance(i.source, hopper.source.meta.GitSource):
					# TODO: fixup pciking of ref name
					refname = "refs/heads/" + i.source.ref
					refpin = None
					if i.source.remote in filtered:
						refs = filtered[i.source.remote]
						if refname in refs:
							refpin = refs[refname]
					newsource = hopper.source.meta.GitSource(i.source.remote, refpin)
				else:
					newsource = i.source
				pinnedlayers.add(i.getFullName(), newsource)
			return pinnedlayers

	def __init__(self, environment):
		self.environment = environment
		self.stop = threading.Event()
		self.thread = None
		self.interval = 0

		self.lock = threading.RLock()
		self.groups = []

		self.changeevent = threading.Condition()
		self.changequeue = []

	def addLayers(self, layers):
		group = Watcher.GroupState(layers)
		self.groups.append(group)

	def start(self, interval = 30):
		if self.thread and self.thread.isAlive():
			return

		self.interval = interval
		self.thread = threading.Thread(target = self.__worker__)
		self.daemon = True
		self.thread.start()

	def stop(self):
		if self.thread and self.thread.isAlive():
			self.stop.set()
			self.thread.join()

	def alive(self):
		if self.thread and self.thread.isAlive():
			return True
		return False

	def trigger(self):
		self.__check__(True)

	def __check__(self, trigger = False):
		with self.lock:
			haschanges = False

			remotes = []
			for i in self.groups:
				for p in i.getRefPairs():
					if p[0] not in remotes:
						remotes.append(p[0])

			self.environment.debug("need to update for the following remotes -> %s" % remotes)

			refstate = {}
			for i in remotes:
				self.environment.log("Grabbing refs from remote for %s" % i)
				result = hopper.utils.git.tasks.GitTask.run(["ls-remote", i], environment = self.environment)
				if result[0] == 0:
					refstate[i] = {}
					for r in result[1].splitlines():
						parts = r.split()
						refstate[i][parts[1]] = parts[0]
					self.environment.debug("got refs -> %s" % repr(refstate[i]))
				else:
					self.environment.error("Failed to get remote state for '%s' error message = %s" % (i, result[1]))
					return

			haschanges = False
			for i in self.groups:
				if i.update(refstate, trigger):
					self.environment.log("Changes have happened since last check, pinning")
					changes = i.cloneRefPin(refstate)
					self.changequeue.append((i.layers, changes, datetime.datetime.utcnow()))
					haschanges = True

		if haschanges:
			with self.changeevent:
				self.changeevent.notifyAll()

	def __worker__(self):
		while not self.stop.wait(self.interval):
			self.__check__()

	def wait(self):
		if self.alive():
			if self.hasnext():
				return

			with self.changeevent:
				self.changeevent.wait()

	def hasnext(self):
		with self.lock:
			if len(self.changequeue) != 0:
				return True
		return False

	def getnext(self):
		with self.lock:
			if len(self.changequeue) != 0:
				return self.changequeue.pop()
		return None

