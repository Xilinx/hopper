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
import stat
import sys
import shutil
import time
import re

from hopper.utils.logger import *

def getFileMTime(file):
	(mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(file)
	return mtime

class SStateMirror:
	@staticmethod
	def updateMirror(environment, mirrorPath, allowchildcache = False):
		sstatepath = os.path.join(environment.getWorkingBuildPath(), "sstate-cache")
		sstatemirrorpath = mirrorPath
		environment.debug("Shared State Path = %s" % sstatepath)
		environment.debug("Shared State Mirror Path = %s" % sstatemirrorpath)

		if not os.access(mirrorPath, os.W_OK):
			environment.warning("The specified mirror does not permit access to update. (Skipping)")
			return True

		if os.path.isdir(sstatepath):
			totalchecked = 0
			ignored = 0
			updated = 0

			files = []
			for i in os.listdir(sstatepath):
				subdir = os.path.join(sstatepath, i)
				if os.path.isdir(subdir):
					for j in os.listdir(subdir):
						if j.endswith(".siginfo"):
							files.append(os.path.join(i, j))
							files.append(os.path.join(i, j.split(".siginfo")[0]))

					# check for child caches (e.g. native ones)
					if allowchildcache:
						for k in os.listdir(subdir):
							childsubdir = os.path.join(sstatepath, i, k)
							if os.path.isdir(childsubdir):
								for j in os.listdir(childsubdir):
									if j.endswith(".siginfo"):
										files.append(os.path.join(i, k, j))
										files.append(os.path.join(i, k, j.split(".siginfo")[0]))

			for i in files:
				sourcefile = os.path.join(sstatepath, i)
				destfile = os.path.join(sstatemirrorpath, i)
				if os.path.isfile(sourcefile):
					totalchecked += 1
					if SStateMirror.updateFile(sourcefile, destfile):
						updated += 1
			environment.log("Shared State Mirror Update: Checked %d files, updated %d (of %d)" % (totalchecked, updated, totalchecked - ignored))
		else:
			environment.error("%s is not a directory." % sstatepath)
			return False
		return True

	@staticmethod
	def updateFile(src, dst):
		if os.path.isfile(src):
			if os.path.isfile(dst):
				srclastchanged = getFileMTime(src)
				dstlastchanged = getFileMTime(dst)
				if srclastchanged > dstlastchanged:
					debug("Updating '%s'" % os.path.basename(src))
					shutil.copyfile(src, dst)
					#updateFilePerms(dst)
					return True
			else:
				debug("Copying '%s'" % os.path.basename(src))
				if not os.path.exists(os.path.dirname(dst)):
					os.makedirs(os.path.dirname(dst))
				shutil.copyfile(src, dst)
				#updateFilePerms(dst)
				return True
		return False

class SourceMirror:
	mirrorwhitelist = [
		".zip",
		".tar",
		".tgz",
		".tar.gz",
		".tar.bz2",
		".tar.lzma",
		".tar.xz",
		".rpm",
		".sh",
		]

	@staticmethod
	def fileAllowed(filename):
		if filename.endswith(".done") or filename.endswith(".lock"):
			# Ignore, bitbake magic files
			return False
		elif filename.endswith(".patch") or filename.endswith(".lock"):
			# Ignore, bitbake magic files
			return False
		elif "bad-checksum" in filename:
			# Ignore
			return False
		else:
			for j in SourceMirror.mirrorwhitelist:
				if filename.endswith(j):
					return True
				elif re.search("bash\d+-\d+", filename): # special case
					return True
			verbose("Ignored '%s'" % os.path.basename(filename))
		return False

	@staticmethod
	def updateMirror(environment, mirrorPath):
		log("Copying Downloads output to mirror")
		downloadsPath = os.path.join(environment.getWorkingBuildPath(), "downloads")
		verbose("Download Path = %s" % downloadsPath)
		verbose("Source Mirror Path = %s" % mirrorPath)

		if not os.access(mirrorPath, os.W_OK):
			warning("The specified source mirror does not permit access to update.")
			log("Skipping mirror update.")
			return True

		if os.path.isdir(downloadsPath):
			totalchecked = 0
			ignored = 0
			updated = 0
			for i in os.listdir(downloadsPath):
				if os.path.isfile(os.path.join(downloadsPath, i)):
					totalchecked += 1
					if SourceMirror.fileAllowed(i):
						if SourceMirror.updateFile(os.path.join(downloadsPath, i), os.path.join(mirrorPath, i)):
							updated += 1
					else:
						ignored += 1
			log("Checked %d files (ignored %d), updated %d (of %d)" % (totalchecked, ignored, updated, totalchecked - ignored))
		else:
			error("%s is not a directory." % downloadsPath)
			return False
		return True

	@staticmethod
	def updateFile(src, dst):
		if os.path.isfile(src):
			if os.path.isfile(dst):
				srclastchanged = getFileMTime(src)
				dstlastchanged = getFileMTime(dst)
				if srclastchanged > dstlastchanged:
					verbose("Updating '%s'" % os.path.basename(src))
					shutil.copyfile(src, dst)
					SourceMirror.updateFilePerms(dst)
					return True
			else:
				verbose("Copying '%s'" % os.path.basename(src))
				shutil.copyfile(src, dst)
				SourceMirror.updateFilePerms(dst)
				return True
		return False

	@staticmethod
	def updateFilePerms(f):
		try:
			os.chmod(f,
					stat.S_IRUSR | stat.S_IWUSR |
					stat.S_IRGRP | stat.S_IWGRP |
					stat.S_IROTH)
		except OSError, e:
			if e.errno == 1:
				warning("Failed to set correct permissions for '%s', owned by another user" % f)
			else:
				error("Failed to set permissions for '%s'" % f)

