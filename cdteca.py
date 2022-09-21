#!/usr/bin/python3
from yaml import safe_load
from urllib.request import urlretrieve
import os.path, getopt, sys, inspect, requests, re

version = "0.0dev8"
confile = os.path.dirname(__file__) + "/config.yaml"
internal_path = os.path.dirname(__file__)
verbose = False
title = "My Cdteca"
path = internal_path + "/data"
ftpc = 2020
ftpd = 2120
httpd = 8020
distros = []

def usage():
    """
    Prints the usage menu.
    """

    print("     cdteca " + version)
    print('Usage: {} [options]\n'.format(os.path.basename(__file__)))
    print('Options:')
    menu = [
        ['-h', '--help', 'show this usage info'],
        ['-s', '--status', 'show status of internal servers'],
        ['-i', '--start', 'init/start servers'],
        ['-f', '--stop', 'finish/stop servers'],
        ['-u', '--update', 'update all distributions'],
        ['-d<name>', '--distro=<name>', 'update a single distro'],
        ['-v', '--verbose', 'enable verbose mode']
    ]
    for ms, mx, md in menu:
        print("{:>10} | {:<18} {}".format(ms, mx, md))

def vprint(msg):
    """
    Print for verbose mode (only if verbose is on).
    """
    if verbose:
        cal = inspect.stack()[1][3]
        sys.stdout.write("\033[0;36m")
        print(cal, end=': ')
        sys.stdout.write("\033[0;0m")
        print(msg)

def update_distro(distro):
    """
    Update a single distro based on distro's recipe.
    """
    
    os.makedirs(path, exist_ok=True)
    """ mkdir -p """

    distfile = internal_path + "/recipes/" + distro + ".distro"
    vprint("Starting checking for {} for distro {}.".format(distfile, distro))
    if os.path.exists(distfile):
        vprint("Loading {} distro recipe.".format(distro))
        with open(distfile) as file:
            dconf = safe_load(file)
            if "url" in dconf and "isoregex" in dconf:
                res = requests.get(dconf['url'])
                if res.status_code == 200:
                    isourl = [m.group(2) for m in re.finditer("(.*)(" + dconf['isoregex'] + ")\"(.*)", res.text)][0]
                    isobase = os.path.basename(isourl)
                    isofile = path + '/' + isobase
                    isotemp = isofile + '-partial'
                    if os.path.exists(isofile):
                        print("Distro {} is up to date: {}".format(distro, isobase))
                    else:
                        vprint("Starting download of iso for {} distro. Wait, it can take time...".format(distro))
                        urlretrieve(isourl, isotemp)
                        vprint("Download complete. Renaming file.")
                        os.rename(isotemp, isofile)
                else:
                    print('Requesting {} results in {} status.'.format(dconf['url'], res.status_code))
    else:
        print("No recipe found for distro {}.".format(distro))

def update_distros():
    """
    Update all distros on internal list.
    """
    for d in distros:
        update_distro(d)

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
        opts, args = getopt.getopt(sys.argv[1:], "hsifud:v", ["help", "status", "start", "stop", "update", "distro", "verbose"] )
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    vprint("called with arguments: " + str(opts))

    for o, a in opts:
        vprint("o=" + o + ", a=" + a)
        if o in ("-v", "--verbose"):
            verbose = True
            vprint("Verbose mode is on")
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-u", "--update"):
            update_distros()
        elif o in ("-d", "--distro"):
            update_distro(a)
    

if __name__ == "__main__":
    main()