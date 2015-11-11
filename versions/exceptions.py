# We will store version exceptions in this file as we
# start defining them.

class VersionContainsNoneGene(Exception):
    def __init__(self, value=None):
        self.value = value
    def __str__(self):
        return repr(self.value)

class NoParentVersionSpecified(Exception):
    def __init__(self, value=None):
        self.value = value
    def __str__(self):
        return repr(self.value)