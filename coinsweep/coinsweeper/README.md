CoinSweeper Command Line Utility
=================

Introduction
------------
The CoinSweeper command line utility is a tool for automating the sweeping
of bitcoin addresses. The destinations of the sweep are also specified.
You can specify the sweep address as a destination, although that wasn't
part of the original idea.

The main reason this was written was to allow the sweeping of paper wallet
and vanity addresses. Once a transaction has sent bitcoins from an address,
the public key of that address has been exposed and the security of that
address is slightly lessened. This utility allows periodic checking of an
address to see if any more bitcoins have been sent to it, and if so sweep
them into a safer location.

This utility has grown into a more general tool as well as potentially an
easier to use library of components that can be used by daemons and GUIs.

**NOTE:** this first version uses the APIs at blockchain.info, and because
of the way they work, the level of security this provides is not the
highest possible. Future versions will provide the ability to use other
services such as a local bitcoind server. For now though, this utility
sends transactions by passing the private key as a URL parameter to
blockchain.info - it does so using HTTPS so casual observers won't be
able to intercept it, but this does mean you will be trusting blockchain
with your private key(s).

Installation
------------
This program is written in Python, so you will need to have a Python 2.7
interpreter installed. It also uses the Crypto library, available at
https://www.dlitz.net/software/pycrypto/ which must be installed separately.

Configuration
-------------
There are two files which will need to be generated. One is a general
configuration file for the program that simply holds the information
needed to encrypt and decrypt the data files. The other file(s) is the
data file that holds the sweep address data.

**NOTE:** the data file(s) will need to hold the private keys of the bitcoin
address(es) being swept, which is why it is encrypted. As no system is
perfectly safe, you should be aware that the safety of your bitcoins
depends on the encryption and especially the pass phrase used. Choose
wisely.

If the configuration file doesn't exist, you will be prompted to create
one, including being asked for a pass phrase. The pass phrase will be
stored in the configuration file, in plain text. If you don't want the
pass phrase to be stored in the configuration file, you will need to
run the program with the '-p' switch; and then you will also need to
remember this pass phrase and enter it every time you run the program.

If the data file doesn't exist, it will be created automatically as an
empty file.

Usage
-----
Please view the help by running
```
./sweepcoins.py --help
```
After you have created the configuration file, you need to create a data
file. Then you need to create the wallet service (for now just the
BlockChain service), add the address(es) you want to watch, then for each
watch address add the destinations.

Addresses being watched and swept need to be specified with their private
keys, so be sure you have those available before starting.

**NOTE:** the listing functionality **will** expose the private keys of
the swept addresses. The danger in this is lessened by the fact that you
are sweeping the addresses regularly, which decreases the window of
opportunity that a thief could use to steal your bitcoins.

Contact Info
------------
This program originally written by Ron Helwig
ron@ronhelwig.com

Donations greatly appreciated at 1BEGAMt5gFWSBiGnHSEDdtUpjUcydzjPkn

