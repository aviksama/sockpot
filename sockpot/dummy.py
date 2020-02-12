from __future__ import unicode_literals
import sys

class Dummy(object):
    @staticmethod
    def writer(data):
        return "received by writer: " + data


def dummy(data):
    return "received: " + data
