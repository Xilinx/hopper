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
import urllib2
import urlparse
import re

from hopper.utils.logger import *

class OELayerIndexCache:
	cache = None
	# TODO: Figure a way to populate these from layer index? (maybe assume subtree is also an alias)
	aliases = {
			"oe-core" : "openembedded-core",
			"meta" : "openembedded-core",
			"core" : "openembedded-core",
			"meta-oe" : "meta-openembedded",
		}
	default = {
			"bitbake" : {
				"remote" : "git://git.openembedded.org/bitbake",
				"bitbake" : True,
			},
		}

	@staticmethod
	def getCache():
		if OELayerIndexCache.cache == None:
			OELayerIndexCache.cache = OELayerIndexCache()
			OELayerIndexCache.cache.update()
		return OELayerIndexCache.cache

	def __init__(self):
		self.layers = {}

	@staticmethod
	def __strip_subdirectory__(webrepo, webrepopath, branch = None):
		cut = webrepopath.replace(webrepo, "")
		# try stripping '/tree/' or '/tree/<branch>/'
		if branch and cut.startswith("/tree/%s/" % branch):
			cut = cut[len("/tree/%s/" % branch):]
		if cut.startswith("/tree/"):
			cut = cut[len("/tree/"):]
		# split of '?h=master' types
		queryparts = cut.split("?", 1)
		if len(queryparts) > 1:
			cut = queryparts[0]
		return cut

	def update(self, branch = "master"):
		note("Updating OpenEmbedded Layer Index (retrieving from layers.openembedded.org)")
		self.layers = {}
		uri = "http://layers.openembedded.org/layerindex/branch/%s/layers/" % branch
		response = urllib2.urlopen(uri)
		data = response.read()
		if data:
			# get the layers table
			m = re.search("<table class=\".*?layerstable.*?\">.*?<tbody>(.*?)</tbody>.*?</table>", data,
					re.MULTILINE | re.DOTALL)
			if m:
				for i in re.finditer("<tr class=\"layertype_.\">(.*?)</tr>", m.group(1), re.MULTILINE | re.DOTALL):
					sections = list(re.finditer("<td.*?>(.*?)</td>", i.group(1), re.MULTILINE | re.DOTALL))
					shortname = None
					if len(sections) >= 1:
						# has shortname
						shortname = re.search("<a.*?>(.*?)</a>", sections[0].group(1), re.DOTALL)
						if shortname:
							shortname = shortname.group(1)
					longname = None
					if len(sections) >= 2:
						longname = sections[1].group(1)
					group = None
					if len(sections) >= 3:
						group = sections[2].group(1)
					remote = None
					webrepo = None
					treepath = None
					if len(sections) >= 4:
						remote = re.search("^\s*(.*?)$", sections[3].group(1), re.MULTILINE | re.DOTALL)
						if remote:
							remote = remote.group(1)
						parts = list(re.finditer("<a.*?href=\"(.*?)\">", sections[3].group(1),
								re.MULTILINE | re.DOTALL))
						if len(parts) >= 1:
							webrepo = parts[0].group(1)
						if len(parts) >= 2:
							treepath = OELayerIndexCache.__strip_subdirectory__(webrepo, parts[1].group(1), branch)

					debug("OEIndex: adding '%s'/'%s' @ %s {%s}" % (shortname, longname, remote, treepath))
					if shortname in self.layers:
						# duplicate
						raise Exception("Got duplicate entry in OE Layer Index")

					info = {
							"shortname" : shortname,
							"description" : longname,
							"remote" : remote,
							"subpath" : treepath,
							}
					self.layers[shortname] = info

	def find(self, name):
		validnames = [name]
		if name in OELayerIndexCache.aliases:
			validnames.append(OELayerIndexCache.aliases[name])

		# Check cache
		for i in validnames:
			if i in self.layers:
				return self.layers[i]

		# Check default values
		for i in validnames:
			if i in OELayerIndexCache.default:
				return OELayerIndexCache.default[i]

		return None

	@staticmethod
	def findRepoNameAlias(name):
		if name in OELayerIndexCache.aliases:
			return OELayerIndexCache.aliases[name]
		return None

def findRepoDetails(name):
	return OELayerIndexCache.getCache().findRepoDetails(name)

def findLayerDetails(name, reponame = None):
	return OELayerIndexCache.getCache().findLayerDetails(name, reponame)

