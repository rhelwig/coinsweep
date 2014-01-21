"""
Created on Jan 7, 2014

:author:     Ron Helwig
:contact:    ron@ronhelwig.com
"""

import json
import urllib
import urllib2
from datetime import datetime, timedelta

#from sweepaddress import SweepAddressInfo, TimeThreshold


__init__ = ["AddressDataBC", "TxnServiceBlockChain"]


def _read_url(url, post_data=None, verbose=False):
    """
    Open a URL, read the contents, and return the result.

    The return is a tuple: (contents, errors), where
    errors is a dictionary.

    """
    contents = ""
    errors = {}
    request = None
    headers = {'User-Agent':\
'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36"\
" (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36'}
    try:
        data = None
        if post_data:
            data = urllib.urlencode(post_data)
        if verbose:
            print "Fetching URL={0}".format(url)
            if data:
                print "With post data ={0}".format(data)
        request = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(request)
        contents = response.read()
        response.close()
    except urllib2.HTTPError as he:
        errors[url] = "HTTP error ({0}): {1}".format(he.code, he.reason)
    except urllib2.URLError as e:
        errors[url] = e.reason
    return (contents, errors)


class AddressDataBC(object):
    """
    Utility class to make fetching data about an address easier

    """

    def __init__(self):
        """
        Probably don't need this

        """

    def fetch_balance(self, address, verbose=False):
        """
        Given an address (as a string), fetch the balance.

        We only want the balance of transactions that have
        6 or more confirmations.

        The return is a tuple: (balance, errors), where
        balance is in satoshis
        errors is a dictionary.
        """

        url = "https://blockchain.info/q/addressbalance/"
        url += address
        url += "?confirmations=6"
        content, errors = _read_url(url, None)
        if errors:
            return (0, errors)
        if verbose:
            print "Retrieved balance of {0}".format(content)
        self.balance = long(content)
        return (self.balance, errors)

    def fetch_unspent_outputs(self, address, verbose=False):
        """
        Given an address, fetch the unspent outputs

        The return is a tuple: (unspent, errors), where
        unspent is a dictionary of the unspent outputs
        errors is a dictionary.

        """
        self.unspent_outputs = None
        url = "https://blockchain.info/unspent?active="
        url += address
        uo_json, errors = _read_url(url, None, verbose)
        if errors:
            return (None, errors)
        if "No free outputs" not in uo_json:
            try:
                self.unspent_outputs = json.loads(uo_json)['unspent_outputs']
            except Exception as e:
                errors[address] = str(e)
        return (self.unspent_outputs, errors)

    def fetch_transactions(self, address, verbose=False):
        """
        Get the latest transactions for this address.

        We will need this to determine if an address has been
        swept more recently than our criteria desires.

        We might also use this to help decide what the transaction
        fee should be. If we need to use more than one input,
        it can make the fee be large. We need to know that before
        we can allocate any destinations.

        The return is a tuple: (txs, errors), where
        unspent is a dictionary of the transactions
        errors is a dictionary.

        """
        self.transactions = None
        url = "https://blockchain.info/rawaddr/"
        url += address
        uo_json, errors = _read_url(url, None, verbose)
        if errors:
            return (None, errors)
        try:
            self.transactions = json.loads(uo_json)['txs']
        except Exception as e:
            errors[address] = str(e)
        return (self.transactions, errors)

    def newest_send(self, address, verbose=False):
        """
        Find the latest datetime when a payment has been sent
        from this address.

        The return is a tuple: (last_send, errors), where
        last_send is a datetime
        errors is a dictionary.

        """
        errors = {}
        if not hasattr(self, 'transactions') or not self.transactions:
            txs, errors = self.fetch_transactions(address, verbose)
            if errors:
                return (datetime.utcfromtimestamp(0), errors)
        else:
            txs = self.transactions

        time = 0
        try:
            for tx in txs:
                tx_time = tx['time']
                inputs = tx['inputs']
                for inp in inputs:
                    prev_out = inp['prev_out']
                    addr = prev_out['addr']
                    if addr == address:
                        if tx_time > time:
                            time = tx_time
        except Exception as e:
            errors[address] = "Failed parsing transactions: {0}".format(str(e))
            return (datetime.utcfromtimestamp(0), errors)

        try:
            dt_result = datetime.utcfromtimestamp(time)
        except Exception as e:
            errors[address] = str(e)
        return (dt_result, errors)

    def fetch_exchange_rate(self, currency, verbose=False):
        """
        Fetch the current exchange rate for the currency

        The return is a tuple: (rate, errors), where
        rate is a float
        errors is a dictionary.

        """
        if verbose:
            print "ENTER AddressDataBC.fetch_exchange_rate"
        rate = 1.0
        url = "https://blockchain.info/ticker"
        ticker_json, errors = _read_url(url, None)
        if errors:
            return (rate, errors)

        try:
            ticker = json.loads(ticker_json)[currency]
            rate = float(ticker['15m'])
        except Exception as e:
            errors[currency] = str(e)
        return (rate, errors)


class TxnServiceBlockChain(object):
    """
    This is one implementation of a Transaction Service.

    This contains the addresses being watched that can be
    processed using this service. In this case the service
    is provided by blockchain.info.

    Implementors should note that this same public interface
    could be used to create a similar class that uses the
    bitcoind service or some other API.

    """

    def __init__(self):
        """
        No real need for this (other than service_name),
        but listing the attributes.

        """
        self.service_name = "BlockChain.info"
        self.watch_list = {}

    def query_info(self):
        """
        No info needed, just let the user know.

        """
        print "This will use BlockChain.info's API."

    def write_info(self, indent="", verbose=False):
        """
        Print out to the standard output this object's
        information, including the addresses being watched
        and all their destinations

        """
        print indent + "=" * len(self.service_name)
        print indent + self.service_name
        print indent + "=" * len(self.service_name)
        for watch in self.watch_list.itervalues():
            watch.write_info("  ", verbose)

    def send_transaction(self,
                         address_info,
                         balance,
                         address_data=AddressDataBC(),
                         verbose=False):
        """
        Given a SweepAddressInfo instance, build the transaction, and send it.

        Returns the resulting transaction hash or an error message as a tuple:
        (address, hash, errors)

        """
        if verbose:
            print "Attempting to calculate and send {0} satoshis from {1}"\
                    .format(balance, address_info.address)
        # Calculate fees and reduce balance by that amount
        # Tx size roughly 148 * number_of_inputs + 34 * number_of_outputs + 10
        # Note: this assumes we are emptying the address
        uo, errors = address_data.fetch_unspent_outputs(address_info.address,
                                                        verbose)
        if errors or not uo:
            return (address_info.address, "", errors)
        input_count = len(uo)
        input_size = 180  # newer ones could be only 148
        output_count = len(address_info.destinations)
        output_size = 34
        header_size = 10
        tx_size = input_size * input_count\
                  + output_size * output_count\
                  + header_size\
                  + input_count  # margin of error
        minimum_fee = 10000
        fees = minimum_fee * long(round(tx_size / 1000 + 0.5))

        # now update our balance so we calculate after paying fees
        balance -= fees
        current_balance = balance
        receiving_balance_count = 0

        # iterate over the send addresses, calculating each one's value
        data = {}  # dictionary to hold JSON data
        btcusd = 0
        for send, amount in address_info.destinations.iteritems():
            if "%" in amount:
                # percentage
                percent = float(amount.strip()[:-1])
                temp_amount = long((balance * percent) / 100)
                data[send] = temp_amount
                current_balance -= temp_amount
                if verbose:
                    print "Sending {0}% ({1}) to {2}".format(percent, temp_amount, send)
            elif "$" == amount[0]:
                # float = dollars, convert to BTC
                dollar_amount = float(amount[1:])
                if 0 == btcusd:
                    # fetch conversion rate (if we haven't already)
                    btcusd, errors = address_data.fetch_exchange_rate("USD",
                                                                      verbose)
                    if errors:
                        return (address_info.address, "", errors)
                    if verbose:
                        print "USDBTC Exchange Rate={0}".format(btcusd)
                # convert temp_amount to satoshis
                temp_amount = dollar_amount / btcusd  # dollars to BTC
                temp_amount = long(temp_amount * 1e8)  # BTC to satoshis
                data[send] = temp_amount
                current_balance -= temp_amount
                if verbose:
                    print "Sending ${0} ({1}) to {2}".format(dollar_amount,
                                                             temp_amount,
                                                             send)
            elif "." in amount:
                # float = bitcoins
                temp_amount = long(round(float(amount) * 1e8))
                data[send] = temp_amount
                current_balance -= temp_amount
                if verbose:
                    print "Sending {0} to {1}".format(temp_amount, send)
            elif long(amount) <= 0:
                # signal balance
                data[send] = 0
                receiving_balance_count += 1
                if verbose:
                    print "Sending balance to {0}".format(send)
            else:
                # satoshis
                data[send] = long(amount)
                current_balance -= long(amount)
                if verbose:
                    print "Sending {0} to {1}".format(long(amount), send)
        # If current balance is negative, we have an error!
        if current_balance < 0:
            # We can't create a valid transaction, bail
            return (address_info.address,
                    "",
                    {address_info.address: \
                     "Error: Insufficient funds for specified payouts!"})
        if receiving_balance_count > 0 and current_balance > 0:
            for send, amount in data.items():
                if amount == 0:
                    data[send] = current_balance / receiving_balance_count
        elif current_balance > receiving_balance_count:
            # there weren't any "balance" destinations and
            # the other destinations don't add up to the balance.
            # If we send, the balance will go to miner's fees,
            # which we probably don't want.
            return (address_info.address,
                    "",
                    {address_info.address: \
                     "Error: Too much in address, need a balance destination" +
                     "(AKA a change address)."})
        try:
            json_values = json.dumps(data)
            url_values = "recipients=" + urllib.quote(json_values)
            note = "&note=Auto+sweep+using+https%3A%2F%2Fgithub.com%2Frhelwig%2Fcoinsweep"
            send_url = "{0}{1}{2}{3}{4}{5}{6}{7}{8}{9}".format(
                                "https://blockchain.info/merchant/",
                                address_info.private_key,
                                "/sendmany?",
                                url_values,
                                "&shared=false",
                                "&fee=",
                                fees,
                                "&from=",
                                address_info.address,
                                note)
        except Exception as e:
            return (address_info.address,
                    "",
                    {address_info.address: \
                     "Error: Failed to construct sending API URL - {0}".format(str(e))})

        # actually send the request
        tx_hash = ""
        response, errors = _read_url(send_url)
        if response:
            try:
                tx_data = json.loads(response)
                if tx_data:
                    tx_hash = tx_data['tx_hash']
            except Exception as e:
                errors[address_info.address] = str(e)
        return (address_info.address, tx_hash, errors)

    def process_transactions(self, verbose=False):
        """
        For each of the addresses in the watch list, send
        their transactions.

        Returns a dictionary of the results.

        """
        r = {}
        for sweep_address in self.watch_list.itervalues():
            if verbose:
                print "Processing {0}".format(sweep_address.address)
            # first check the balance
            fetcher = AddressDataBC()
            balance, errors = fetcher.fetch_balance(sweep_address.address,
                                                    verbose)
            if errors:
                r[sweep_address.address] = json.dumps(errors)
                continue
            if balance > sweep_address.balance_threshold:
                # check the time criteria
                most_recent, errors = fetcher.newest_send(sweep_address.address,
                                                          verbose)
                if errors:
                    r[sweep_address.address] = json.dumps(errors)
                    continue
                if verbose:
                    print "Most recent send time: {0}".format(most_recent)
                if most_recent == datetime.utcfromtimestamp(0):
                    if verbose:
                        print "no sends from this address yet"
                    # we haven't sent from this address yet
                    a, m, errors = self.send_transaction(sweep_address,
                                                 balance,
                                                 fetcher,
                                                 verbose)
                    if m:
                        r[a] = m
                    else:
                        r[a] = errors
                else:
                    if verbose:
                        print "Checking most recent send"
                    # we need to check the most recent send
                    # add a margin of error (say 5 minutes)
                    elapsed_time = datetime.utcnow() - most_recent
                    elapsed_time = elapsed_time + timedelta(minutes=5)
                    if verbose:
                        print "elapsed time(+ margin)={0}".format(elapsed_time)
                    # elapsed_time should be a datetime.timedelta object
                    if sweep_address.time_threshold.waited_enough(elapsed_time,
                                                                  verbose):
                        a, m, errors = self.send_transaction(sweep_address,
                                                     balance,
                                                     fetcher,
                                                     verbose)
                        if m:
                            r[a] = "Success, Tx=".format(m)
                        else:
                            r[a] = errors
                    else:
                        r[sweep_address.address] = "Not enough time elapsed"
            else:
                r[sweep_address.address] = "Balance not large enough"
        return r
