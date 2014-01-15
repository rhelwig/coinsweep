"""
Created on Jan 7, 2014

:author:     Ron Helwig
:contact:    ron@ronhelwig.com
"""

from datetime import datetime, timedelta

__all__ = ["SweepAddressInfo", "TimeThreshold"]


class TimeThreshold(object):
    """
    What sort of time threshold?

    This needs to be able to handle criteria like
    - monthly
    - weekly
    - daily
    - hourly
    - specified intervals
    - don't wait at all

    """

    def __init__(self):
        self.duration = "P1D"  # default to one day

    def query_info(self):
        """
        Interactively get the time threshold info

        """
        years = abs(int(raw_input("How many years?")))
        months = int(raw_input("How many months?"))
        while months not in range(0, 13):
            months = int(raw_input("How many months (0-12)?"))
        weeks = int(raw_input("How many weeks?"))
        while weeks not in range(0, 53):
            weeks = int(raw_input("How many weeks? (0-52)"))
        days = int(raw_input("How many days?"))
        while days not in range(0, 32):
            days = int(raw_input("How many days? (0-31)"))
        hours = int(raw_input("How many hours?"))
        while hours not in range(0, 25):
            hours = int(raw_input("How many hours? (0-24"))
        # convert it to an ISO 8601 Duration
        self.duration = "P{0}Y{1}M{2}W{3}D{4}H".format(years,
                                                       months,
                                                       weeks,
                                                       days,
                                                       hours)
        return

    def write_info(self, indent="", verbose=False):
        """
        Write the threshold data to the console

        """
        print indent + "ISO 8601 duration: {0}".format(self.duration)
        return

    def waited_enough(self, waited, verbose):
        """
        Check to see if the duration passed in as 'waited'
        is longer than the threshold in self.duration.

        This is a very naive implementation, assuming months
        are 30 days long and years are 365 days. We could
        make it account for months and years more accurately,
        but this utility is intended to be used for shorter
        periods than those anyway. Probably good enough, and
        if anyone really cares they'll likely be coding their
        own solution.

        """
        if verbose:
            print "Duration of {0}".format(self.duration)
        wait = timedelta()
        index = self.duration.find("Y")
        if index > 0:
            val = int(self.duration[index - 1:index])
            wait = wait + timedelta(years=val)
        index = self.duration.find("M")
        if index > 0:
            val = int(self.duration[index - 1:index])
            wait = wait + timedelta(months=val)
        index = self.duration.find("W")
        if index > 0:
            val = int(self.duration[index - 1:index])
            wait = wait + timedelta(weeks=val)
        index = self.duration.find("D")
        if index > 0:
            val = int(self.duration[index - 1:index])
            wait = wait + timedelta(days=val)
        index = self.duration.find("H")
        if index > 0:
            val = int(self.duration[index - 1:index])
            wait = wait + timedelta(hours=val)
        if verbose:
            print "Duration comparison is {0}".format(waited > wait)
        return waited > wait


class SweepAddressInfo(object):
    """
    The data needed for an address being watched for sweeping.

    self.destinations is a dictionary of
    address => send_amount
    where send_amount is a string
    - N.M%: a float with a suffix of %
    - N: an integer number of satoshis
    - N.M: a float number of BTC
    - $N.M: a float number of dollars
    - zero: balance of amount being sent

    """

    def __init__(self):
        """
        Constructor - basically lists the members
        and creates a time threshold instance.

        """

        self.address = ''
        self.private_key = ''
        self.time_threshold = TimeThreshold()
        self.balance_threshold = 0
        self.destinations = {}

    def query_info(self):
        """
        Interactively query the user for the data this needs.

        """
        # TODO: add some input validation here!
        self.address = raw_input("What is the address being watched?")
        self.private_key = raw_input("What is its private key?")
        btc = raw_input("Minimum balance when it should be swept (in btc)?")
        self.balance_threshold = long(round(float(btc) * 1e8))
        # conversion back to btc from satoshi is "float(amount / 1e8)"
        self.time_threshold.query_info()

    def write_info(self, indent="", verbose=False):
        """
        Write this object's data to standard out.

        """
        print indent + "-" * len(self.address)
        print indent + self.address
        print indent + "-" * len(self.address)
        indent = indent + "  "
        print indent + "private key:{0}".format(self.private_key)
        self.time_threshold.write_info(indent, verbose)
        print indent + "Balance Threshold (in satoshis): {0}"\
                        .format(self.balance_threshold)
        print indent + "Balance Threshold (in bitcoins): {0}"\
                        .format(float(self.balance_threshold / 1e8))
        for send_address, send_amount in self.destinations.iteritems():
            amount = send_amount.strip()
            if "%" in amount[-1]:
                print indent + "# {0} gets {1} percent".format(send_address,
                                                        amount[:-1])
            elif "$" == amount[0]:
                print indent + "# {0} gets {1}".format(send_address,
                                                        amount)
            elif "." in amount:
                print indent + "# {0} gets {1} bitcoins".format(send_address,
                                                        amount)
            elif long(amount) == 0:
                print indent + "# {0} gets the balance".format(send_address,
                                                        amount)
            else:
                print indent + "# {0} gets {1} satoshis".format(send_address,
                                                        amount)
