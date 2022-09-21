#!/usr/bin/python3
from yaml import safe_load
import os.path, getopt, sys, inspect

version = "0.0dev5"
confile = os.path.dirname(__file__) + "/config.yaml"
verbose = False
title = "My Cdteca"
path = os.path.dirname(__file__) + "/data"
ftpc = 2020
ftpd = 2120
httpd = 8020
distros = []

def usage():
    print("     cdteca " + version)
    print('Usage: {} [options]\n'.format(os.path.basename(__file__)))
    print('Options:')
    menu = {
        '-h | --help': 'show this usage info',
        '-s | --status': 'show status of internal servers',
        '-i | --start': 'init/start servers',
        '-f | --stop': 'finish/stop servers',
        '-u | --update': 'update all distributions',
        '-v | --verbose': 'enable verbose mode'
    }
    for mk in menu:
        print("{:<15} {}".format(mk, menu[mk]))

def vprint(msg):
    if verbose:
        cal = inspect.stack()[1][3]
        sys.stdout.write("\033[0;36m")
        print(cal, end=': ')
        sys.stdout.write("\033[0;0m")
        print(msg)

def main():
    global verbose, title, path, ftpc, ftpd, httpd, distros

    if os.path.exists(confile):
        with open(confile, 'r') as file:
            cdconf = safe_load(file)
            vprint("Loaded: " + str(cdconf))
            if "title" in cdconf:
                title = cdconf['title']
            if "path" in cdconf:
                path = cdconf['path']
            if "ftp-ports" in cdconf:
                ftpc = cdconf['ftp-ports'][0]
                ftpd = cdconf['ftp-ports'][1]
            if "http-port" in cdconf:
                httpd = cdconf['http-port']
            if "distros" in cdconf:
                distros = cdconf['distros']
            if "verbose" in cdconf:                
                verbose = cdconf['verbose']
                vprint('Verbose enabled by conf file')
    else:
        print("Configuration file {} not found.".format(confile))
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hsifuv", ["help", "status", "start", "stop", "update", "verbose"] )
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    for o, a in opts:
        vprint("o=" + o + ", a=" + a)
        if o in ("-v", "--verbose"):
            verbose = True
            vprint("Verbose mode is on")
        elif o in ("-h", "--help"):
            usage()
            sys.exit()            
    
    vprint("called with arguments: " + str(opts))

if __name__ == "__main__":
    main()