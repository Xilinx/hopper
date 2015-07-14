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

import sys
import os
import re

from hopper.utils.logger import *

class BitBakeScanner:
	@staticmethod
	def scanLayerConfVersion(environment, layers):
		layerDefaultVersion = 6
		layerVersions = {}
		# Scan all layers for bblayers sample
		for i in layers:
			# Special parsing for 'meta' layer
			if i.getName() == "meta":
				expectedSanityPath = os.path.join(i.getSourcePath(environment), "conf", "sanity.conf")
				if os.path.isfile(expectedSanityPath):
					layerDefaultVersion = BitBakeScanner.scanFileForLayerConfVersion(expectedSanityPath)
					debug("BitBakeScanner: Default 'meta' Layer vesion = %s" % layerDefaultVersion)

		for i in layers:
			distroPath = os.path.join(i.getSourcePath(environment), "conf", "distro")
			if os.path.isdir(distroPath):
				layerdefault = layerDefaultVersion
				missing = []
				for c in os.listdir(distroPath):
					if c.endswith(".conf"):
						name = os.path.splitext(c)[0]
						path = os.path.join(distroPath, c)
						debug("BitBakeScanner: Distro found in Layer '%s' at %s" % (i.getName(), path))
						lconfversion = BitBakeScanner.scanFileForLayerConfVersion(path)
						layerVersions[name] = lconfversion
						if lconfversion == None:
							missing.append(name)
						if layerdefault == None and lconfversion != None:
							layerdefault = lconfversion

				for m in missing:
					layerVersions[m] = layerdefault

		if layerDefaultVersion == None:
			warning("BitBakeScanner: Default Layer Version cannot be determined defaulting to 0")
			layerDefaultVersion = 0

		return (layerDefaultVersion, layerVersions)

	@staticmethod
	def scanFileForLayerConfVersion(filepath):
		if os.path.isfile(filepath):
			with open(filepath, "r") as sampleFile:
				match = re.search("LAYER_CONF_VERSION.*=.*\"(\\d+)\"", sampleFile.read())
				if match:
					version = int(match.group(1))
					return version
		return None
