#!/usr/bin/python3
from yaml import safe_load
from urllib.request import urlretrieve

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

import os.path, getopt, sys, inspect, requests, re, hashlib

version = "0.0dev12"
confile = os.path.dirname(__file__) + "/config.yaml"
internal_path = os.path.dirname(__file__)
verbose = False
title = "My Cdteca"
path = internal_path + "/data"
checksum_method = "md5"
ftp = {
    'com': 2020,
    'data': 2120,
    'user': "cdteca",
    'password': "cdteca"
}
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
        ['-l', '--list', 'list all supported distros'],
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

def check_sum(file, type):
    """
    Checksum for downloaded file, using different algorithms.
    """
    if os.path.exists(file):
        if type == "sha512":
            hasha = hashlib.sha512()
            hasha.update( open(file, 'rb').read())
            return hasha.hexdigest()
    else:
        print("File {} do not exists!".format(file))

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
                        vprint("Download complete.")

                        res = requests.get(dconf['checksum'])
                        remsum = [m.group(1) for m in re.finditer("(.*)" + isobase, res.text)][0].strip()
                        if check_sum(isotemp, dconf['method']) == remsum:
                            vprint("Checksum validated. All is fine!")
                            os.rename(isotemp, isofile)
                        else:
                            print("Checksum don't match. Aborting...")
                            os.remove(isotemp)
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
    
    build_checksums()
    build_index()

def build_checksums():
    """
    Create or update a checksum file.
    """

    vprint("Initializing checksum file creation. Method: {}.".format(checksum_method))

    checkfile = open(path + "/" + checksum_method + ".txt" , "w")

    for fn in os.listdir(path):
        if fn.endswith(".iso"):
            if checksum_method == "sha512":
                hasha = hashlib.sha512()
            hasha.update( open(path + '/' + fn, 'rb').read())
            checkfile.write(hasha.hexdigest() + " " + fn)
    checkfile.close()

def build_index():
    """
    Create an HTML linking the files.
    """

    chklink = "<a href='{}.txt'>Checksum</a>".format(checksum_method)

    htfile = open(path + "/index.html" , "w")
    htfile.write("<html><head><title>{}</title></head>".format(title))
    htfile.write("<body><h1>{}</h1><div class='note'>{}</div>".format(title, chklink))
    htfile.write("<ul>")
    for fn in os.listdir(path):
        if fn.endswith(".iso"):
            htfile.write("<li><a href='{}'>{}</a></li>".format(fn, fn))
    htfile.write("</ul></body></html>")
    htfile.close()    

def ftpd():
    """
    FTP server.
    """
    authorizer = DummyAuthorizer()

    # Define a new user having full r/w permissions.
    authorizer.add_user(ftp['user'], ftp['password'], path, perm='elradfmw')

    handler = FTPHandler
    handler.authorizer = authorizer

    # Define a customized banner (string returned when client connects)
    handler.banner = "Cdteca {} ftp, powered by pyftpdlib, ready."

    # Optionally specify range of ports to use for passive connections.
    #handler.passive_ports = range(60000, 65535)

    address = ('', ftp['com'])
    server = FTPServer(address, handler)

    server.max_cons = 256
    server.max_cons_per_ip = 5

    server.serve_forever()

def main():
    global verbose, title, path, ftpc, ftpd, httpd, distros, checksum_method

    if os.path.exists(confile):
        with open(confile, 'r') as file:
            cdconf = safe_load(file)
            if "title" in cdconf:
                title = cdconf['title']
            if "path" in cdconf:
                path = cdconf['path']
            if "ftp-ports" in cdconf:
                ftp['com'] = cdconf['ftp-ports'][0]
                ftp['data'] = cdconf['ftp-ports'][1]
                if "ftp-user" in cdconf:
                    ftp['user'] = cdconf['ftp-user']
                if "ftp-password" in cdconf:
                    ftp['password'] = cdconf['ftp-password']
            if "http-port" in cdconf:
                httpd = cdconf['http-port']
            if "distros" in cdconf:
                distros = cdconf['distros']
            if "checksum-method" in cdconf:
                checksum_method = cdconf["checksum-method"]
            if "verbose" in cdconf:                
                verbose = cdconf['verbose']
                vprint("Loaded: " + str(cdconf))
    else:
        print("Configuration file {} not found.".format(confile))
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hsifud:vl", ["help", "status", "start", "stop", "update", "distro", "verbose", "list"] )
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
        elif o in ('-i', '--start'):
            ftpd()
    

if __name__ == "__main__":
    main()