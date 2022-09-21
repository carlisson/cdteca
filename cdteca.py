#!/usr/bin/python3
from yaml import safe_load
import os.path

version = "0.0dev2"
confile = os.path.dirname(__file__) + "/config.yaml"

if os.path.exists(confile):
    with open(confile, 'r') as file:
        cdconf = safe_load(file)
        print(cdconf)
else:
    print("Configuration file " + confile + " not found.")
