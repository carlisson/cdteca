# Cdteca
Cdteca is a simple ISO library downloader/manager.
## Why?
Main usage is to keep a local ISO library of GNU/Linux distributions and other operating systems to use as a storage for Proxmox. Other uses includes human access in intranet.
## Features
* Configuration in a yaml file, listing distributions to download.
* Check new version of distros and update
* Test the checksum of downloaded iso
* FTP server included
* HTML output (you can put iso path under a web server)
* Generate checksum for all ISO in one text file for HTML output
* Distro instructions in recipe (yaml) files
* Recipes available: debian (only this for now)
## To-Do
* Improve HTML output with style
* Improve HTML output with more information
* Recipes for other distros
* Resume downloads
* Localization
* Distro listing (based on distrowatch)
## Dependences
To version 0.1, you need to install:
* Python 3
* pyftpdlib
Other libraries: getopt, hashlib, inspect, os, re, requests, sys, urllib, yaml.
## Install
There is not an installer yet, but you can download cdteca and run it.
You can clone it via github or download the version 0.1.
After download, you need to change config.yaml.
## Usage
* **python3 cdteca.py -h**: show all options.
* **python3 cdteca.py -u**: download/update distros and build HTML and checksum files.
* **python3 cdteca.py -d**: run FTP server.