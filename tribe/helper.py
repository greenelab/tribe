"""This file includes some helper function."""

from ConfigParser import RawConfigParser
from os.path import join, normpath


def get_config(config_dir, filename):
    """Parses config_dir/filename and returns the configuration.

    The ini files are parsed by RawConfigParser (instead of ConfigParser
    or SafeConfigParser) to avoid "%" interpolation when an option's
    value includes "%" character (such as password strings).  See more
    details at: https://docs.python.org/2/library/configparser.html

    If the input file has "[include]" section, also reads that included
    file from config_dir directory.  The final configuration will be a
    combination of these two files.  If an option is specified in both
    the input file and the config file, the former will always take
    precedence over the latter.
    """
    secrets = RawConfigParser()
    secrets.read(normpath(join(config_dir, filename)))

    # If input file doesn't have "[config file]" section, we're done.
    if not secrets.has_section('include'):
        return secrets

    included_filename = secrets.get('include', 'FILE_NAME')
    extra_config = RawConfigParser()
    extra_config.read(normpath(join(config_dir, included_filename)))

    merged_config = extra_config
    for section in secrets.sections():
        if not merged_config.has_section(section):
            merged_config.add_section(section)
        for key, value in secrets.items(section):
            merged_config.set(section, key, value)

    return merged_config
