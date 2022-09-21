#!/usr/bin/python3
from yaml import safe_load
import os.path, getopt, sys

version = "0.0dev3"
confile = os.path.dirname(__file__) + "/config.yaml"

def usage():
    print("Usage instructions.")

def main():

    if os.path.exists(confile):
        with open(confile, 'r') as file:
            cdconf = safe_load(file)
            #print("Loaded: " + str(cdconf))
    else:
        print("Configuration file " + confile + " not found.")
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hsifu", ["help", "status", "start", "stop", "update"] )
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

if __name__ == "__main__":
    main()