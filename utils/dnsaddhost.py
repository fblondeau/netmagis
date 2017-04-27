#!/usr/bin/env python3

#
# Syntax:
#   dnsaddhost <fqdn> <ip> <viewname>
#
# This scripts uses a configuration file for authentication purpose
#   ~/.config/netmagisrc
#       [general]
#           url = https://app.example.com/netmagis
#           key = a-secret-key-delivered-by-netmagis
#

import argparse

from nmcli.core import netmagis

def main ():
    parser = argparse.ArgumentParser (description='Netmagis add host')
    parser.add_argument ('-c', '--config-file', action='store',
                help='Config file location (default=~/.config/netmagisrc)')
    parser.add_argument ('fqdn', help='Host FQDN')
    parser.add_argument ('ip', help='IP (v4 or v6) address to add')
    parser.add_argument ('view', help='View name')

    args = parser.parse_args ()
    if args.config_file is None:
        configfile = netmagis.default_conf_filename ()

    fqdn = args.fqdn
    ip = args.ip
    view = args.view

    nm = netmagis ()
    try:
        nm.read_conf (configfile)
    except RuntimeError as m:
        netmagis.grmbl (m)

    (name, domain, iddom) = nm.split_fqdn (fqdn)
    if name is None:
        netmagis.grmbl ('Invalid FQDN {}'.format (fqdn))
    if iddom is None:
        netmagis.grmbl ('Unknown domain {}'.format (domain))

    idview = nm.get_idview (view)
    if not idview:
        netmagis.grmbl ('Unknown view {}'.format (view))

    #
    # Test if host already exists
    #

    query = {'name': name, 'domain': domain, 'view': view}
    r = nm.api ('get', '/hosts', params=query)
    netmagis.test_answer (r)

    j = r.json ()
    nr = len (j)
    if nr == 0:
        #
        # Host does not exist: use a POST request to create the jost
        #

        # TODO : find a way to get a default HINFO value (API change requested)
        idhinfo = 0

        data = {
                    'name': name,
                    'iddom': iddom,
                    'idview': idview,
                    'mac': "",
                    'idhinfo': idhinfo,
                    'comment': "",
                    'respname': "",
                    'respmail': "",
                    'iddhcpprof': -1,
                    'ttl': -1,
                    'addr': [ip],
                }
        r = nm.api ('post', '/hosts', json=data)
        netmagis.test_answer (r)

    elif nr == 1:
        #
        # Host already exists: get full data with an additional GET
        # request for this idhost, and use a PUT request to add the
        # new IP address
        #

        idhost = j [0]['idhost']
        uri = '/hosts/' + str (idhost)
        r = nm.api ('get', uri)
        netmagis.test_answer (r)

        data = r.json ()
        data ['addr'].append (ip)
        r = nm.api ('put', uri, json=data)
        netmagis.test_answer (r)

    else:
        # this case should never happen
        msg = "Server error: host '{}.{}' exists more than once in view {}"
        netmagis.grmbl (msg.format (name, domain, view))

if __name__ == '__main__':
    main ()
