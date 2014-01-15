"""
cryptconfig - defines CryptConfig class

CryptConfig is a helper class. It stores the data needed to
read and write encrypted files in a config file.

Created on Jan 5, 2014

:author:     Ron Helwig
:contact:    ron@ronhelwig.com
"""

import os
import errno
import pickle
import getpass

# This next library needs to be installed
#    download from https://www.dlitz.net/software/pycrypto/
#    install by using sudo python setup.py install (on Linux)
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random

__all__ = ['CryptConfig']


def _derive_key(passphrase, salt, key_length, iv_length):
    """
    Helper function to create a properly sized password.
    The AES functionality we use to encrypt requires that the password be
    an exact length. We use SHA256 to generate the real password from the
    user's pass phrase which is passed in as ``passphrase``.

    """
    d = ''
    d_i = ''

    # key length can be a tuple, if so we need to use only one value
    if isinstance(key_length, tuple):
        key_length = max(key_length)

    enc = SHA256.new()
    while len(d) < key_length:
        enc.update(d_i + passphrase + salt)
        d_i = enc.hexdigest()
        d += d_i
    return d[:key_length]


def _ensure_path(path):
    if not os.path.exists(os.path.dirname(path)):
        # create the directory
        try:
            os.makedirs(os.path.dirname(path))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise


class CryptConfig(object):
    """
    Holds the basic config info needed to read and write encrypted files.
    Allows reading and writing of files.
    ``self.passphrase`` is a text pass phrase to be converted into a properly
    sized password.
    ``self.iv`` is the initialization vector needed by the cipher.

    """

    def __init__(self, file_, passphrase):
        """
        Constructor
        ``file_`` parameter is the config file to be read or created.
        ``passphrase`` is a user entered pass phrase or blank. If blank and
        there is no file, ask user for it on command line and save it in
        the file - so if using this from a GUI you HAVE to pass one in
        if the file doesn't exist!
        ``file_`` will be created with reasonable defaults if it doesn't exist.

        """
        self.passphrase = ''
        self.iv = ''

        # make sure our config file exists
        if '~' in file_:
            # its in the user data directory
            cf = os.path.expanduser(file_)
        else:
            cf = os.path.abspath(file_)

        d = {}
        override_pass = False
        if os.path.exists(cf):
            # read existing config file
            if passphrase:
                override_pass = True
            with open(cf) as cfg_file:
                d = pickle.loads(cfg_file.read())
            if override_pass:
                d['passphrase'] = passphrase
        else:
            if not passphrase:
                pass_ask = "Enter a pass phrase (will be stored)"
                d['passphrase'] = getpass.getpass(pass_ask)
            else:
                override_pass = True
                d['passphrase'] = "no passphrase"
            # we need to generate a new config file and the data to go in it
            d['iv'] = Random.new().read(AES.block_size)
            _ensure_path(cf)
            with open(cf, 'w') as config:
                config.write(pickle.dumps(d))
            if override_pass:
                d['passphrase'] = passphrase

        self.passphrase = d['passphrase']
        self.iv = d['iv']

    def read_encrypted_file(self, file_):
        """
        Reads ``file_``, decrypts it, and returns it as a string

        """
        s = ""
        if os.path.exists(file_):
            with open(file_, 'rb') as ef:
                es = ef.read()
                # decrypt s
                key = _derive_key(self.passphrase,
                                  self.iv,
                                  AES.key_size,
                                  AES.block_size)
                cipher = AES.new(key, AES.MODE_CBC, self.iv)
                s = cipher.decrypt(es)
        return s

    def write_encrypted_file(self, file_, s):
        """
        Encrypt string ``s`` and write it to ``file_``

        """
        key = _derive_key(self.passphrase,
                          self.iv,
                          AES.key_size,
                          AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, self.iv)
        padding = " " * (AES.block_size - (len(s) % AES.block_size))
        es = cipher.encrypt(s + padding)
        with open(file_, 'wb') as ef:
            ef.write(es)
