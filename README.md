Hopper
======
Hopper is a utility specifically designed to prepare and configure bitbake builds for Yocto/OpenEmbedded.

Getting Started
===============
Hopper can do a number of different things, for more information on a specific command or command usage use the help command.

```shell
$ hopper help
```

Example Build
=============
An example is provided below which describes how to prepare a bitbake build configuration for the 'qemumicroblaze' machine using Poky and meta-xilinx, build the 'core-image-minimal' target.

In a empty directory (recommended that the directory is on local disk, e.g. in /tmp) execute the following command.

```shell
$ hopper -l:meta -l:meta-yocto -l:meta-xilinx --distro=poky \
    --machine=qemumicroblaze core-image-minimal
```
