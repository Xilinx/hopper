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
from hopper.utils.Proxy import *
import hopper.utils.path

from BitBakeScanner import *

class Configuration:
	def __init__(self, layers = None):
		self.threadLimit = None

		self.machine = None
		self.distro = None
		self.devmode = False
		self.hopperEnv = True

		self.layers = layers

		self.vars = []

	def setTargetMachine(self, machine):
		self.machine = machine

	def setDistro(self, distro):
		self.distro = distro

	def setThreadLimit(self, threads):
		self.threadLimit = threads

class ConfigurationGenerator:
	def __init__(self, environment, config):
		self.environment = environment
		self.config = config

	def generate(self, overwrite = True):
		basepath = self.environment.getWorkingPath()
		self.environment.debug("Creating configuration root directory")
		confroot = os.path.join(basepath, "conf")
		if not os.path.isdir(confroot):
			os.makedirs(confroot)

		conffiles = self.generateConfs()
		for i in conffiles.iteritems():
			confpath = os.path.join(confroot, i[0])
			if (os.path.exists(confpath) and i[0] == "local.conf" and not(overwrite)):
				self.environment.note("%s already exists, preserving it" % i[0])
			else:
				confdata = i[1].formatToStr()
				self.environment.debug("Writing %s" % i[0])
				with open(confpath, "w") as conffile:
					conffile.write(confdata)

		return True

	def generateConfs(self):
		conffiles = {}
		conffiles["bblayers.conf"] = self.generateLayer()
		conffiles["local.conf"] = self.generateLocal()
		conffiles["environment.conf"] = self.generateEnvironment()

		return conffiles

	def generateLayer(self):
		bblayers = hopper.utils.bitbake.config.BBConfig()

		# determine the expected bblayers version
		deflayerversions = BitBakeScanner.scanLayerConfVersion(self.environment, self.config.layers)
		if self.config.distro and self.config.distro in deflayerversions[1]:
			bblayers.add("LCONF_VERSION", "=", deflayerversions[1][self.config.distro])
		elif deflayerversions[0]:
			bblayers.add("LCONF_VERSION", "=", deflayerversions[0])

		with bblayers.section("Directories") as conf:
			conf.add("ROOTDIR", ":=", "${TOPDIR}")
			conf.add("TOPDIR", ":=", "${ROOTDIR}/build")
			conf.add("TMPDIR", "=", "${TOPDIR}/tmp")

		with bblayers.section("Layers") as conf:
			conf.add("BBPATH", "=", "${ROOTDIR}")
			conf.add("BBFILES", "?=", "")

			layers = " \\\n"
			for i in self.config.layers:
				if not i.isBitBake() and i.getName() != "test":
					layerpath = i.getSourcePath(self.environment)
					layers += "  %s \\\n" % hopper.utils.path.switchrelpath(layerpath,
							self.environment.getWorkingPath(), "${ROOTDIR}")
			conf.add("BBLAYERS", "?=", layers)

		return bblayers

	def generateEnvironment(self):
		conf = hopper.utils.bitbake.config.BBConfig()

		# General options
		conf.add("PATCHRESOLVE", "=", "noop")

		with conf.section("System") as sconf:
			if self.config.threadLimit:
				sconf.add("BB_NUMBER_THREADS", "=", self.config.threadLimit)
				sconf.add("PARALLEL_MAKE", "=", "-j %d" % self.config.threadLimit)

		if self.environment and self.environment.getProxy():
			proxy = self.environment.getProxy()
			with conf.section("Proxy") as pconf:
				# Setup an override on wget
				pconf.add("FETCHCMD_wget", "=", "/usr/bin/env wget -t 10 --timeout=3600 -nv --passive-ftp --no-check-certificate")
				# Setup an override on git, also setup the exports for when using the buildtools
				pconf.add("FETCHCMD_git", "=", "git -c core.gitproxy=%s" % Proxy.getProxyTunnelCommand())
				pconf.add("GIT_SSL_CAINFO[export]", "=", "1")
				pconf.add("GIT_SSL_CAPATH[export]", "=", "1")
				# Setup an override on svn
				#pconf["FETCHCMD_svn"] = "svn --config-option servers:global:http-proxy-host=%s --config-option servers:global:http-proxy-port=%s" % (proxy.getProxyHost(), proxy.getProxyPort())

		if self.environment.getDownloadMirrorUri():
			self.environment.note("Using source mirror '%s'" % self.environment.getDownloadMirrorUri())
			with conf.section("Mirror") as mconf:
				mconf.add("SOURCE_MIRROR_URL", "?=", self.environment.getDownloadMirrorUri())
				mconf.add("INHERIT", "+=", "own-mirrors")
				# only enable this if any source mirror is used, otherwise it is unlikely that the user want tarballs
				mconf.add("BB_GENERATE_MIRROR_TARBALLS", "?=", "1")

		if not self.config.devmode:
			self.environment.note("Applying standard build configuration optimizations")
			with conf.section("Optimization") as oconf:
				oconf.add("INHERIT", "+=", "rm_work")

		return conf

	def generateLocal(self):
		conf = hopper.utils.bitbake.config.BBConfig()

		# conf version
		conf.add("CONF_VERSION", "=", "1")

		# includes hopper environment context
		if self.config.hopperEnv:
			conf.addRequire("conf/environment.conf")

		with conf.section("Defaults") as dconf:
			# default configuration values
			dconf.add("EXTRA_IMAGE_FEATURES", "=", "debug-tweaks")

			if self.config.machine:
				dconf.add("MACHINE", "?=", self.config.machine)
			if self.config.distro:
				dconf.add("DISTRO", "?=", self.config.distro)

		with conf.section("Configs") as cconf:
			if self.config.vars:
				for i in self.config.vars:
					cconf.add(i[0], i[1], i[2])

		return conf

# Simple class for storing conf/recipe style data
class BBConfig:
	# Wrapper for easy additions to specific sections
	class BBConfigSection:
		def __init__(self, bbconfig, section):
			self.bbconfig = bbconfig
			self.section = section

		def add(self, var, operator, value):
			self.bbconfig.add(var, operator, value, self.section)

		def addRequire(self, path):
			self.bbconfig.addRequire(path, self.section)

		def __enter__(self):
			return self

		def __exit__(self ,type, value, traceback):
			pass

	def __init__(self):
		self.config = []
		self.sections = [None]

	def add(self, var, operator, value, section = None):
		self.config.append((var, operator, value, section))
		if section and section not in self.sections:
			self.sections.append(section)

	def addRequire(self, path, section = None):
		self.config.append((None, "require", path, section))
		if section and section not in self.sections:
			self.sections.append(section)

	def section(self, section):
		return BBConfig.BBConfigSection(self, section)

	@staticmethod
	def formatConfig(name, operator, value ="", spacing = True):
		if operator == "require":
			return BBConfig.formatRequire(value)
		elif name != None:
			return BBConfig.formatVar(name, operator, value, spacing)
		return None

	@staticmethod
	def formatVar(name, operator = "=", value = "", spacing = True):
		configname = name
		configvalue = value
		if spacing:
			return "%s %s \"%s\"" % (name, operator, configvalue)
		else:
			return "%s%s\"%s\"" % (name, operator, configvalue)

	@staticmethod
	def formatRequire(value):
		return "require %s" % value

	def formatToStr(self):
		filedata = ""
		for i in self.sections:
			if i != None:
				filedata += "\n"
				filedata += "# %s\n" % i

			for j in self.config:
				if j[3] == i:
					data = BBConfig.formatConfig(j[0], j[1], j[2])
					if data != None:
						filedata += data + "\n"

		return filedata
