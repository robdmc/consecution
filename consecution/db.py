import django
import importlib
from django.conf import settings
from django.core.management import call_command


# #############################################################################
#  NOTE:  I REALLY COULDN'T FIGURE OUT HOW TO COVER THIS FUNCTION
#         BECAUSE I DON'T KNOW HOW TO FAKE DJANGO INTO THINKING NO SETTING
#         HAVE BEEN CONFIGURED.  IT IS NOT 100% COVERED WITH TESTS.
# #############################################################################
def configure_default_settings_if_needed(sqlite_file):  # pragma: no cover
    """
    Function to set up django if it hasn't been set up
    """

    # don't do anything if django has already been configured
    if settings.configured:
        return

    if sqlite_file is None:
        msg = '\n\nA sqlite file name must be supplied if brain app is not installed in a django project.\n'
        raise ValueError(msg)

    # configure the db
    db_config = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': sqlite_file,
    }

    settings.configure(
        DATABASES={
            'default': db_config,
        },
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.admin',
            'brain',
        ),
        TEST_RUNNER='django_nose.NoseTestSuiteRunner',
        NOSE_ARGS=['--nocapture', '--nologcapture', '--verbosity=1'],
        ROOT_URLCONF='brain.urls',
        DEBUG=False,
        MIDDLEWARE_CLASSES=(),
    )

    # set up django and call syncdb
    django.setup()
    call_command('migrate', verbosity=0)


def get_backend_global(name, sqlite_file):
    """
    Function to return any variable from the global name_space of models.py
    This is needed to properly navigate the order in which imports and
    django_setup are executed in the factories module.
    """
    configure_default_settings_if_needed(sqlite_file)
    module = importlib.import_module('brain.models')
    return getattr(module, name)
