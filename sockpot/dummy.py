from __future__ import unicode_literals
import sys

class Dummy(object):
    @staticmethod
    def writer(data):
        return "received: " + data + "\n"


def dummy(data):
    return "received: " + data + "\n"
