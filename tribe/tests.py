from django.test import TestCase
from os.path import dirname, join, normpath
from helper import get_config

class ConfigTest(TestCase):
    def setUp(self):
        self.current_dir = dirname(__file__)

    def test_merged_config(self):
        config_dir = normpath(join(self.current_dir, "config"))
        filename = 'unit_test_secrets.ini'
        config = get_config(config_dir, filename)

        # Test options that are specified only in 'unit_test_secrets.ini'
        self.assertEqual(config.get('secrets', 'SECRET_KEY'), 'k#%(x)s$y')
        self.assertEqual(config.get('database', 'DATABASE_PASSWORD'), 'bbb')

        # Test options that are specified only in the included file.
        self.assertEqual(config.get('database', 'DATABASE_USER'), 'tribe')
        self.assertEqual(config.get('database', 'DATABASE_PORT'), '5432')

        # Test options that are specified in both unit_test_secrets.ini
        # and its included file. (unit_test_secrets.ini should always
        # take precedence.)
        self.assertEqual(config.get('database', 'DATABASE_HOST'), 'aaa')
        self.assertEqual(config.get('debug', 'ALLOWED_HOSTS'),
                         'localhost 127.0.0.1')
