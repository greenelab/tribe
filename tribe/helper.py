"""This file includes some helper functions."""

from ConfigParser import RawConfigParser
from os.path import join, normpath


def get_config(config_dir, filename):
    """Parses <filename> from <config_dir> and returns configuration.

    <filename> is assumed to be in `ini` format, and is parsed by
    RawConfigParser (instead of ConfigParser or SafeConfigParser) to
    avoid accidental '%' interpolation when an option's value includes
    '%' character (such as password strings).  Please see more details
    at: https://docs.python.org/2/library/configparser.html

    If "[include]" section exists in <filename> and the value of
    "FILE_NAME" option in this section is not empty, also read included
    file from <config_dir> directory.  The final configuration will be
    a combination of these two files.  For options that are specified in
    both <filename> and included file, values in <filename> will always
    take precedence.
    """
    config = RawConfigParser()
    config.read(normpath(join(config_dir, filename)))

    # If "[include]" section exists, and its "FILE_NAME" option is not
    # empty, parse the "FILE_NAME" in ini format and merge its values
    # into config.
    if config.has_section('include') and config.get('include', 'FILE_NAME'):
        included_filename = config.get('include', 'FILE_NAME')
        secondary_config = RawConfigParser()
        secondary_config.read(normpath(join(config_dir, included_filename)))
        for section in secondary_config.sections():
            if not config.has_section(section):
                config.add_section(section)
            for option, value in secondary_config.items(section):
                if not config.has_option(section, option):
                    config.set(section, option, value)

    return config
