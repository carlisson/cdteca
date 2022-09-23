# Cdteca
Cdteca is a simple ISO library downloader/manager.

![misc/screenshot-0.2.png](Cdteca 0.2 HTML output, with cyan theme)

## Why?
Main usage is to keep a local ISO library of GNU/Linux distributions and other operating systems to use as a storage for Proxmox. Other uses includes human access in intranet.

## Features
* Configuration in a yaml file, listing distributions to download.
* Check new version of distros and update
* Test the checksum of downloaded iso
* FTP server included
* HTML output (you can put iso path under a web server)
* Theme support for HTML (available: simple and cyan)
* Generate checksum for all ISO in one text file for HTML output
* Distro instructions in recipe (yaml) files
* Recipes available: debian fedora fedora-server mint mx ubuntu ubuntu-server

## To-Do
* Recipes for other distros
* Resume downloads
* Localization

## Dependences
To version 0.2, you need to install:
* Python 3
* pyftpdlib
Other libraries: getopt, hashlib, inspect, os, re, requests, sys, urllib, yaml.

## Install
There is not an installer yet, but you can download cdteca and run it.
You can clone it via github or download the version 0.2.
After download, you need to change config.yaml.

## Usage
* **python3 cdteca.py -h**: show all options.
* **python3 cdteca.py -u**: download/update distros and build HTML and checksum files.
* **python3 cdteca.py -d**: run FTP server.