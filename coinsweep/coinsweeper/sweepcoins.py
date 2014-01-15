#!/usr/bin/env python
# encoding: utf-8
"""
coinsweeper.main -- command line interface to coin sweeper

coinsweeper.main is a tool for automating the sweeping of bitcoins
from an address to a set of addresses based on specifiable criteria.

:author:     Ron Helwig
:copyright:  Copyright is an invalid concept, and we'll have none of that
:license:    Use as you wish
:contact:    ron@ronhelwig.com
"""

import sys
import os
import getpass
import pickle
from argparse import ArgumentParser, RawDescriptionHelpFormatter

from cryptconfig import CryptConfig
from sweepblockchain import TxnServiceBlockChain, AddressDataBC
from sweepaddress import SweepAddressInfo

__all__ = []
__version__ = 0.5
__date__ = '2014-01-04'
__updated__ = '2014-01-14'

DEBUG = 0
TESTRUN = 0
PROFILE = 0


class CLIError(Exception):
    """Generic exception to raise and log different fatal errors."""
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return self.msg


def _save_data(data, cfg, file_):
    """Quick helper function, encrypts then saves cfg to file_"""
    s = pickle.dumps(data)
    cfg.write_encrypted_file(file_, s)


def _query_add_service(service_list):
    """Interactively have the user select a service type and input its data"""
    #TODO: when we have more services (such as bitcoind)
    # then we need to add them here and let the user select which one to use
    service = TxnServiceBlockChain()
    if service.service_name in service_list:
        print "This will overwrite the existing {0} service!".format(service.service_name)
        go_on = raw_input("Continue? (y/n): ")
        if "Y" not in go_on.upper():
            print "Aborting service add"
            return None
    # note: this will overwrite any existing TxnServiceBlockChains
    service.query_info()
    service_list[service.service_name] = service
    return service


def _query_select_service(service_list):
    """Interactively have the user select a service from the service list"""
    if len(service_list) < 1:
        return None
    elif len(service_list) < 2:
        return service_list.values()[-1]
    else:
        selection = 0
        while selection == 0:
            # repeat until we get a valid service
            print "Choose the service to use."
            i = 1
            d = {}
            for service in service_list.values():
                print "{0}: {1}".format(i, service.service_name)
                d[i] = service
                i += 1
            choice = int(raw_input("Enter the number: "))
            if choice in d:
                selection = choice
        return d[int(selection)]


def _query_add_watch(service):
    """Interactively have the user input the watch address info."""
    address_info = SweepAddressInfo()
    address_info.query_info()
    service.watch_list[address_info.address] = address_info
    return address_info


def _query_select_watch(service):
    """Interactively have the user select a SweepAddressInfo from service."""
    if len(service.watch_list) < 1:
        return None
    elif len(service.watch_list) < 2:
        return service.watch_list.values()[-1]
    else:
        selection = 0
        while selection == 0:
            print "Choose the sweep address."
            i = 1
            a = {}
            for sweep_address in service.watch_list.values():
                print "{0}: {1}".format(i, sweep_address.address)
                a[i] = sweep_address.address
                i += 1
            choice = int(raw_input("Enter the number: "))
            if choice in a:
                selection = choice
        return service.watch_list[a[selection]]


def _query_add_send(watch_info):
    """Interactively ask user for info on new send addresses."""
    send_address = raw_input("What address to send to? ")
    print("You can specify the amount as:")
    print(" - a percentage: X%")
    print(" - satoshis: N")
    print(" - bitcoins: N.M")
    print(" - dollars: $N.M")
    print(" - split the remaining balance: 0")
    print("If more than one send to address is 'balance',\
 the balance will be split evenly between them.")
    send_amount = raw_input("How much? ")
    watch_info.destinations[send_address] = send_amount


def main(argv=None):  # IGNORE:C0111
    """Command line options."""

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (
                                program_version,
                                program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by Ron Helwig on %s.
  Copyright is an invalid concept.

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))
    program_epilog = '''If you find this program useful,
donations of bitcoins are appreciated at
1BEGAMt5gFWSBiGnHSEDdtUpjUcydzjPkn
Any donations received at this address will be routinely swept.
'''
    program_file_help = '''Encrypted data file containing the
addresses to be watched as well as all the info about where and
how much to send bitcoins. (default: %(default)s)
NOTE: This file will necessarily contain information that will allow
the sending of bitcoins automatically. This file is encrypted using a
passphrase, so the safety of your bitcoins depends on the strength of
the passphrase used.
'''
    program_config_help = '''Configuration file, (default: %(default)s)
If this file does not exist, the user will be asked to enter a passphrase,
the initialization vector will be generated, and the file will be created.

The config file contains a text passphrase and an initialization vector for the
encryption functionality used to keep the data file safe. If -p is specified
then the user will be asked to enter the passphrase manually, but the
initialization vector from the file will still be used.
'''
    program_passphrase_help = '''Flag to indicate passphrase will be
entered interactively and not stored in the config file (default: %(default)s)
WARNING: If the passphrase is not stored it must be remembered or the
data file will be unreadable.
'''
    program_addservice_help = '''Flag indicating the program is to
interactively ask the user for a new service's information. The service
is the way that the transactions are created and information about
addresses is found.
'''
    program_addwatch_help = '''Flag indicating that the program is to
interactively ask the user for information about an address to watch.
Values queried include the address, the minimum balance before sweeping,
and the minimum time between sweeps.
'''
    program_destination_help = '''Flag indicating that the program is to
interactively ask the user for information about an address to add
to an existing watched address as a destination for the swept bitcoins.
'''
    program_list_help = '''Print out the data file, showing which
addresses are being watched and where they are configured to send,
along with the criteria of each.
Warning: This will expose the private key of the watched addresses.
'''

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license,
                                formatter_class=RawDescriptionHelpFormatter,
                                epilog=program_epilog)
        parser.add_argument("-v",
                            "--verbose",
                            dest="verbose",
                            action="count",
                            help="output more detailed information")
        parser.add_argument('-V',
                            '--version',
                            action='version',
                            version=program_version_message)
        parser.add_argument('-p',
                            '--password',
                            dest="get_pass",
                            action='store_true',
                            help=program_passphrase_help)
        parser.add_argument('-c',
                            '--config',
                            dest="config",
                            help=program_config_help,
                            default="~/.config/coinsweep/config.txt")
        parser.add_argument('-f',
                            '--file',
                            dest="data_file",
                            help=program_file_help,
                            default="bitcoinsweep.dat")
        add_group = parser.add_mutually_exclusive_group()
        add_group.add_argument('-s',
                            '--addservice',
                            dest="add_service",
                            action='store_true',
                            help=program_addservice_help)
        add_group.add_argument('-a',
                            '--addwatch',
                            dest="add_watch",
                            action='store_true',
                            help=program_addwatch_help)
        add_group.add_argument('-d',
                            '--destination',
                            dest="add_destination",
                            action='store_true',
                            help=program_destination_help)
        parser.add_argument('-l',
                            '--list',
                            dest="list_addresses",
                            action='store_true',
                            help=program_list_help)

        # Process arguments
        args = parser.parse_args()

        verbose = args.verbose

        if verbose > 0:
            print "Verbose mode on"
            print "Configuration file: {0}".format(args.config)
            print "Data file: {0}".format(args.data_file)

        if args.get_pass:
            pass_ask = "Enter a pass phrase (won't be stored in config file)"
            passphrase = getpass.getpass(pass_ask)
        else:
            passphrase = ""

        cfg = CryptConfig(args.config, passphrase)
        if DEBUG:
            print "Pass phrase: {0}".format(cfg.passphrase)

        # read the data file, creating the object hierarchy
        # Note: it is possible the file doesn't exist yet,
        # but only if there was an error creating cfg.
        sweep_data = cfg.read_encrypted_file(args.data_file)
        if sweep_data:
            service_list = pickle.loads(sweep_data)
        else:
            service_list = {}

        if args.add_service:
            # query user for info to add a new wallet service
            _query_add_service(service_list)
            _save_data(service_list, cfg, args.data_file)
            return 0

        if args.add_watch:
            service = {}
            if not service_list:
                service = _query_add_service(service_list)
            else:
                while not service:
                    service = _query_select_service(service_list)
            # query user for info to add a new address to watch
            _query_add_watch(service)
            _save_data(service_list, cfg, args.data_file)
            return 0

        if args.add_destination:
            service = {}
            if not service_list:
                service = _query_add_service(service_list)
                watch_info = _query_add_watch(service)
            else:
                while not service:
                    service = _query_select_service(service_list)
                if not service.watch_list:
                    watch_info = _query_add_watch(service)
                else:
                    watch_info = _query_select_watch(service)
            _query_add_send(watch_info)
            _save_data(service_list, cfg, args.data_file)
            return 0

        if args.list_addresses:
            for service in service_list.itervalues():
                service.write_info("", verbose)
            return 0

        # process the data file
        for service in service_list.itervalues():
            r = service.process_transactions(args.verbose)
            for address, result in r.iteritems():
                print "{0}: {1}".format(address, result)

        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception, e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-v")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'coinsweeper.main_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())
