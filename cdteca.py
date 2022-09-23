#!/usr/bin/python3
from yaml import safe_load
from urllib.request import urlretrieve
from datetime import datetime

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

import os.path, getopt, sys, inspect, requests, re, hashlib, jinja2, shutil

version = "0.1dev8"
confile = os.path.dirname(__file__) + "/config.yaml"
internal_path = os.path.dirname(__file__)
verbose = False
retains = True
title = "My Cdteca"
path = os.path.abspath(internal_path + "/../cdteca-data")
checksum_method = "md5"
ftp = {
    'port': 2020,
    'user': "cdteca",
    'password': "cdteca"
}
html_theme = "simple"
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
        ['-u', '--update', 'update all distributions'],
        ['-D', '--daemon', 'Start FTP service'],
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

def humansize(nbytes):
    """
    Converts bytes to human readable format.
    """
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '{} {}'.format(f, suffixes[i])

def extract_info(url, regex, position = 0, group = 2):
    """
    Find a expression in a HTML URL.
    @param url to catch
    @param full regular expression, defyning groups.
    @param position in HTML
    @param group catched, based on regular expression
    """
    res = requests.get(url)
    if res.status_code == 200:
        outp = [m.group(group) for m in re.finditer(regex, res.text)][position]
        vprint("Applying regex {} in {}, it was found: {}.".format(regex, url, outp))
        return outp
    else:
        print("url {} returned status code {}.".format(url, res.status_code))
    return ""    

def check_sum(file, type):
    """
    Checksum for downloaded file, using different algorithms.
    """
    if os.path.exists(file):
        if type == "sha512":
            hasha = hashlib.sha512()
        elif type == "md5":
            hasha = hashlib.md5()
        elif type =="sha256":
            hasha = hashlib.sha256()
        hasha.update( open(file, 'rb').read())
        resul = hasha.hexdigest()
        vprint("checksum of {} with type {} resulted in {}".format(file, type, resul))
        return resul
    else:
        print("File {} do not exists!".format(file))

def iso_clear(iso, patt):
    """
    Remove old versions of iso if "retains" is False.
    """
    if not retains:
        vprint("Checking old files for {}.".format(iso))
        for fn in os.listdir(path):
            if re.match(patt, fn):
                if fn != iso:
                    os.remove(path + '/' + fn)
                    vprint("{} removed.".format(fn))

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
                
                # isopos is the position of iso in download page. Mint don't works with fist link (403 error)
                if "isoposition" in dconf:
                    isopos = dconf['isoposition']
                else:
                    isopos = 0
                
                isourl = extract_info(dconf['url'], "(.*)(" + dconf['isoregex'] + ")[\"\'](.*)", isopos)
                res = requests.get(dconf['url'])
                if isourl != "":

                    isobase = os.path.basename(isourl)
                    if isourl == isobase:
                        isourl = re.sub('\?(.*)', '', dconf['url']) + '/' + isobase
                    isocheck = dconf['checksum'].replace('@', isourl)
                    if not re.match('^(http|https|ftp)', isocheck):
                        isocheck = isourl.replace(isobase, isocheck)
                    isofile = path + '/' + isobase
                    isotemp = isofile + '-partial'
                    vprint("General: distro {} from {}. File is {}, checksum is {}. Temp is {}.".format(distro, isourl, isobase, isocheck, isotemp))

                    if os.path.exists(isofile):
                        print("Distro {} is up to date: {}".format(distro, isobase))
                        iso_clear(isobase, dconf["localregex"])
                    else:
                        vprint("Starting download of iso for {} distro. Wait, it can take time...".format(distro))
                        
                        urlretrieve(isourl, isotemp)
                        vprint("Download complete.")

                        remsum = extract_info(isocheck, "(.*) (.*)" + isobase, group=1)
                        if check_sum(isotemp, dconf['method']) == remsum:
                            vprint("Checksum validated. All is fine!")
                            os.rename(isotemp, isofile)
                            iso_clear(isobase, dconf["localregex"])
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
            checkfile.write(check_sum(path + '/' + fn, checksum_method) + " " + fn + os.linesep)
    checkfile.close()

def build_index():
    """
    Create an HTML linking the files.
    """

    chklink = "<a href='{}.txt'>Checksum</a>".format(checksum_method)
    templpath = internal_path + '/templates/' + html_theme
    
    vprint("Trying to build HTML from {}.".format(templpath))
    if os.path.exists(templpath):
        loader = jinja2.FileSystemLoader(templpath)
        env = jinja2.Environment(loader=loader)
        template = env.get_template('index.j2')

        
        dists = []
        for fn in sorted(os.listdir(path)):
            if fn.endswith(".iso"):
                dt = datetime.fromtimestamp(os.path.getctime(path + '/' + fn))

                dists.append(dict(name=fn, link=fn, date=dt.strftime("%Y-%m-%d"),
                    size=humansize(os.path.getsize(path + '/' + fn)) ))

        template.render(title=title, checksum=chklink, files=dists)
        htfile = open(path + "/index.html" , "w")
        htfile.write(template.render(title=title, checksum=chklink, files=dists))
        htfile.close()

        # Replace theme files
        themepath = path + '/plus'
        if os.path.exists(themepath):
            shutil.rmtree(themepath)
        os.makedirs(themepath)
        for fn in os.listdir(templpath):
            if not fn.endswith(".j2"):
                shutil.copyfile(templpath + "/" + fn, themepath + '/' + fn)
    else:
        print("Template {} not found.".format(html_template))
    

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

    address = ('', ftp['port'])
    server = FTPServer(address, handler)

    server.max_cons = 256
    server.max_cons_per_ip = 5

    server.serve_forever()

def main():
    global verbose, title, path, ftp, distros, checksum_method, html_theme, retains

    if os.path.exists(confile):
        with open(confile, 'r') as file:
            cdconf = safe_load(file)
            if "title" in cdconf:
                title = cdconf['title']
            if "path" in cdconf:
                path = cdconf['path']
            if "ftp-ports" in cdconf:
                ftp['port'] = cdconf['ftp-port']
                if "ftp-user" in cdconf:
                    ftp['user'] = cdconf['ftp-user']
                if "ftp-password" in cdconf:
                    ftp['password'] = cdconf['ftp-password']
            if "html-theme" in cdconf:
                html_theme = cdconf['html-theme']
            if "distros" in cdconf:
                distros = cdconf['distros']
            if "checksum-method" in cdconf:
                checksum_method = cdconf["checksum-method"]
            if "retains" in cdconf:
                retains = cdconf['retains']
            if "verbose" in cdconf:                
                verbose = cdconf['verbose']
                vprint("Loaded: " + str(cdconf))
    else:
        print("Configuration file {} not found.".format(confile))
        sys.exit(1)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "huDd:vl", ["help", "update", "daemon", "distro", "verbose", "list"] )
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
        elif o in ('-D', '--daemon'):
            ftpd()
    

if __name__ == "__main__":
    main()