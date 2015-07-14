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

from CommandHopperBase import *
import hopper.utils.args
import hopper.utils.bitbake.config

import hopper.source.meta
import hopper.source.fetcher
import hopper.source.LayerDefaultRemotes

from BuildTask import *

class CommandBake(CommandHopperBase):
	CommandName = ["bake", "build"]

	# Layer Source options
	layers = hopper.utils.args.RepositoryOption(
			"l", "layer",
			multiple = True,
			valueoptional = True,
			keyname = "layer",
			description = "Select a layer to be sourced and added to the BitBake build.\n\n" +
				"The layer should be specified using its name and if required its repository.\n" +
				"e.g. 'meta-networking' of the 'meta-oe' repository would be: 'meta-oe/meta-networking'. (Some remotes can be automatically determined)\n\n" +
				"Ther version specifier accepts valid git refs '<branch>[:<commit-id>]'." +
				"Alternatively the 'local' version can be used to specify the use of a repository/layer, this creates a symlink to the local path instead of performing a checkout.\n\n" +
				"If the version is not specified it will use the version of the repository or the default version.")
	version = hopper.utils.args.ValueOption(
			"v", "version",
			default = "master",
			description = "The default reference specifier for layers/repositories.")
	forceupdate = hopper.utils.args.BooleanOption(
			"b", "remote-bleeding",
			default = False,
			description = "Forces the update of repositories, ensuring that the local cache and clone are at the newest version.")

	# Configuration
	distro = hopper.utils.args.ValueOption(
			None, "distro",
			default = None,
			multiple = False,
			description = "The distribution that is to be built by the environment.")
	machine = hopper.utils.args.ValueOption(
			None, "machine",
			default = "qemuzynq",
			multiple = False,
			description = "The target machine to be built.")
	variableoverrides = hopper.utils.args.PairOption(
			None, "var",
			default = {},
			multiple = True,
			validoperators = ["??=", "+=", "?=", "-=", "=+", "=-"],
			description = "Override or append additional options to the local.conf.")
	environmentoverrides = hopper.utils.args.PairOption(
			None, "envvar",
			default = {},
			multiple = True,
			description = "Overrides environment variables when executing bitbake.")

	# Deploy Options
	deployImages = hopper.utils.args.ValueOption(
			None, "deploy-images",
			description = "Once the build is complete, copy all deployable images to that specified directory.")

	# Execution options
	updateMirror = hopper.utils.args.BooleanOption(
			None, "update-mirror",
			description = "Once the build is complete update the source mirror if specified.")
	subshell = hopper.utils.args.BooleanOption(
			None, "subshell",
			default = False,
			multiple = False,
			description = "Instead of running the associated bitbake command, run open subshell within the bitbake environment instead.\n\n" +
				"(Uses the default 'SHELL' environment variable, or bash)")
	devmode = hopper.utils.args.BooleanOption(
			None, "devmode",
			default = False,
			multiple = False,
			description = "Run bitbake/etc with development configuration options.\n\n" +
				"(This will affect build performance and or disk utilization)")
	preserveconfig = hopper.utils.args.BooleanOption(
			"p", "preserve-config",
			default = False,
			multiple = False,
			description = "When preparing the build environment, if a local.conf or bblayers.conf already exist preserve them in their current state.")

	# Targets
	targets = hopper.utils.args.Parameter("targets", multiple = True, index = 0)

	# Helper args
	# providerLinuxDummy = BooleanOption(None, "linux-dummy-provider",
	# 		description = "Override virtual/kernel provide to be 'linux-dummy' so that no kernel is sourced or compiled.")
	# externaltoolchain = ValueOption("t", "external-toolchain",
	# 		description = "The location to a external Xilinx toolchain (which supports the Architecture/Machine specified).")
	# noNetwork = BooleanOption(None, "no-network",
	# 		description = "Disable network access within the BitBake environment. (This does not disable hopper's access)")

	def __init__(self):
		CommandHopperBase.__init__(self)

	def getConfiguration(self):
		# generate layer data
		metalayers = hopper.source.meta.LayerCollection(self.version)
		metalayers.addIndex(hopper.source.LayerDefaultRemotes.OELayerIndexCache.getCache())
		metalayers.parse(self.layers)
		metalayers.validate()

		# Configuration
		configuration = hopper.utils.bitbake.config.Configuration(metalayers)
		configuration.setThreadLimit(self.environment.getMaxThreads())
		configuration.setTargetMachine(self.machine)
		configuration.setDistro(self.distro)
		configuration.devmode = self.devmode

		# Pass Through Variable Options
		configuration.vars = self.variableoverrides

		return configuration

	def execute(self, handler = None):
		CommandHopperBase.execute(self)

		# TODO: map the helper args to override
		buildtask = BuildTask(self.environment, self.getConfiguration())
		buildtask.subshell = self.subshell
		buildtask.updateMirror = self.updateMirror
		buildtask.overwriteconfig = not(self.preserveconfig)
		buildtask.targets = self.targets

		# default to subshell mode if no targets
		if (not self.targets or len(self.targets) <= 0) and not (self.subshell):
			warning("No bitbake targets provided, assuming subshell")
			buildtask.subshell = True

		buildtask.execute()
		return True

