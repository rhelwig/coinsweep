"""
The coinsweeper package can be used to 'sweep' bitcoins
from specified bitcoin addresses to sets of other addresses.

Why
===
There are many reasons why you would want to automatically
sweep coins from a known address, but most importantly is that
it can improve the security of the coins. Once a transaction
has happened from an address, its public key is now known.
This means that the private key can theoretically be determined.
While this is not a current threat, if some future cryptographer
should succeed in breaking ECDSA then moving bitcoins to unused
addresses will become more important.

Other possible uses for this are
- automate shared payment schemes such as shared tips
- sweep vanity addresses to better store addresses
- ensure paper wallets get emptied once used and never get reused permanently
- recurring payments
- - in bitcoins but based on dollars
- tithing
- business processing

Command Line
============
The command line interface (in sweepcoins.py) can be used to
- generate watch files that hold the data needed to sweep an address
- add to existing watch files
- list the contents of a watch file
- run a sweep operation on the set of watch addresses in a watch file

Other
=====
The watch file is used to specify when an address is swept, by checking
a threshold value as well as a minimum time between sweeps. The
addresses to sweep to can be specified with a percentage, a fixed
amount, in dollars, or as the balance after the other addresses have
been sent to.

The classes in this package can be used to build utilities that have
graphical interfaces or are daemons/services. In those cases be aware
that functions and methods with prefixes "query_" and "write_" use
the console for input and output and should not be called. They do,
however, serve as example code. All other functions and methods should
be usable in non-console programs.

You can, of course, send the balance back to the sending address.

:author:     Ron Helwig
:contact:    ron@ronhelwig.com

"""

__all__ = ["sweepcoins", "cryptconfig", "sweepaddress", "sweepblockchain"]
