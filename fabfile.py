# -*- coding: utf-8 -*-
"""
Manage Tribe instances.

This provides the fab commands required to setup and
update imstances on a remote environment (e.g. the amazon
cloud).
"""

from fabric.api import abort
from fabric.api import cd
from fabric.api import env
from fabric.api import execute
from fabric.api import prefix
from fabric.api import run
from fabric.api import settings
from fabric.api import task
from fabric.api import put
from fabric.contrib.console import confirm
from fabric.operations import prompt
from django.utils.crypto import get_random_string


class Helpers(object):

    """
    Utility methods for tribe tasks.

    This class provides methods that perform tasks that are useful in
    server setup and maintainence.
    """

    class Django(object):
        @staticmethod
        def generate_secret_key():
            values = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$^&*(-_=+)'
            key = get_random_string(50, values)
            return key


@task
def get_secret_key():
    """
    Generate a secret key.

    This utility method generates a secret key for django. Use this key
    when required.
    """
    print Helpers.Django.generate_secret_key()


# Where the app lives on the server
WEB_LOCATION = '/home/tribe/tribe'
# Configuration for the production envuronment
PROD_CFG = {
    'dir': WEB_LOCATION,
    'virt_env': '/home/tribe/.virtualenvs/tribe',
    'service': 'tribe',
}


def _check_env():
    """
    Ensure that this is an existing deployment that we are updating.

    Pass in directory via env.dir.
    """
    if not env.dir:
        abort('Set env.dir')
    with settings(warn_only=True):
        if run('test -d {0}'.format(env.dir)).failed:
            abort('Not yet set up - set up environment')
        else:
            run('python {0}/manage.py check'.format(WEB_LOCATION))
            print('Environment seems to exist - good!')


@task
def initial_setup_and_check():
    """
    Setup initial needs for server.

    This command executes an initial pip install from the production
    environment and then checks the current environment to make sure that
    there is an existing django project.
    """
    env.dir = PROD_CFG['dir']
    env.virt_env = PROD_CFG['virt_env']
    with cd(env.dir), prefix('source {0}/bin/activate'.format(env.virt_env)):
        execute(_pip_install)
        execute(_make_static)
        execute(_check_env)


def _hg_pull():
    """
    Pull from mercurial.

    Pull code from repo, to 'tag' if supplied, or else tip.
    """
    tag_name = prompt(
        'To what tag should we pull (default "tip")?',
        default="tip",)
    run('hg pull && hg checkout -C {tag} && hg update'.format(
        tag=tag_name,
    ))


def _pip_install():
    """
    Run pip install for production.

    Run pip install using the requirements file associated with
    the production environment (requirements/prod.txt).
    """
    run('pip install -q -r requirements/prod.txt')


def _make_static():
    """
    Symlink for staticfiles.

    For deployment, this should point to interface/bin (essentially if DEBUG=False)
    For development, this should point to interface/build (DEBUG=True)
    """
    run('ln -s interface/bin static')


def _migrate():
    """
    Run django's migrate command.

    Ensure that all database changes are applied.
    """
    run('python {0}/manage.py migrate'.format(WEB_LOCATION))


def _restart():
    """
    Restart the service on the server.

    You must have setup sudo for the supervisorctl restart tribe command. See the
    setup fab file.
    """
    run('sudo supervisorctl restart tribe')


def _bower():
    """
    Run bower install.

    Install any new required or potentially updated packages from packages.json.
    """
    run('bower install')


def _grunt():
    """
    Run grunt commands.

    Grunt allows us to build the source files from the individual components. The 
    compile command  combines angular files to a single javascript file and creates
    the integrated index.html file (used when DEBUG = False).
    """
    run('grunt build --force')  # Use force b/c testing environment not around.
    run('grunt compile --force')  # Use force b/c testing environment not around.


def _update_search_indexes(app_name=None):
    """
    Update haystack search indexes. If an app name is passed, it will only
    update the indexes for that app. If no app name is passed, it will update
    the indexes for ALL apps that have search indexes.
    """

    if app_name:
        run('python {0}/manage.py update_index {1}'.format(WEB_LOCATION, app_name))
    else:
        run('python {0}/manage.py update_index'.format(WEB_LOCATION))


def _run_deploy(_cfg=None):
    """
    Run the specified deployment.

    Wrapper around a set of private methods for each step of the deploy.
    """
    if not _cfg:
        abort('Must set parameters for deploy, use particular script')
    env.dir = _cfg['dir']
    env.virt_env = _cfg['virt_env']
    env.service = _cfg['service']

    with cd(env.dir), prefix('source {0}/bin/activate'.format(env.virt_env)):
        execute(_check_env)
        execute(_hg_pull)
        execute(_pip_install)
        execute(_migrate)

    import os
    with cd(os.path.join(env.dir, 'interface')):
        execute(_bower)
        execute(_grunt)

    with cd(env.dir), prefix('source {0}/bin/activate'.format(env.virt_env)):
        execute(_restart)


@task
def deploy():
    """
    Deploy to production.

    This runs the set of deployment methods. This checks the environment,
    pulls updates from mercurial, pip-installs production, migrates, and
    then restarts the tribe instance using supervisorctl.
    """
    if not confirm('You are deploying to production. Do you mean to be?'):
        abort('Aborting at user request')

    _run_deploy(PROD_CFG)


@task
def add_organism(_cfg=PROD_CFG, taxid=None, name=None, species_name=None):
    """
    Add an organism to the database.

    Executes the management command to add an organism on the remote
    server.
    """
    if not _cfg:
        abort('Must set parameters for deploy, use particular script')
    env.dir = _cfg['dir']
    env.virt_env = _cfg['virt_env']
    env.service = _cfg['service']

    if not taxid and name and species_name:
        abort('Must set all three options (taxid, name, species_name)')
    with cd(env.dir), prefix('source {0}/bin/activate'.format(env.virt_env)):
        run('python manage.py organisms_add_organism --tax_id={0} --name="{1}" --species_name="{2}"'.format(taxid, name, species_name))


@task
def add_xrdb(_cfg=PROD_CFG, name=None, url=None):
    """
    Add a crossreference database.

    Executes the management command to add a crossreference database
    on the remote server.
    """
    print(url)
    if not _cfg:
        abort('Must set parameters for deploy, use particular script')
    env.dir = _cfg['dir']
    env.virt_env = _cfg['virt_env']
    env.service = _cfg['service']
    if not name and url:
        abort('Must set both options (name, url)')
    with cd(env.dir), prefix('source {0}/bin/activate'.format(env.virt_env)):
        run('python manage.py genes_add_xrdb --name={0} --URL="{1}"'.format(name, url))


@task
def load_geneinfo(_cfg=PROD_CFG, geneinfo=None, genestxt=None, taxid=None, gi_taxid=None, symbol=None, systematic=None, alias=None, uniquexrdb=None):
    """
    Load genes from ncbi on the remote server.

    Upload a geneinfo file, load its contents using the associated management
    command.
    """
    if not _cfg:
        abort('Must set parameters for deploy, use particular script')
    env.dir = _cfg['dir']
    env.virt_env = _cfg['virt_env']
    env.service = _cfg['service']

    if geneinfo is None:
        abort('No gene_info file was passed. Please download one from: ftp://ftp.ncbi.nih.gov/gene/DATA/GENE_INFO/')
    run('mkdir -p ~/uploads')
    gi = put(geneinfo, '~/uploads/')[0]

    if genestxt is not None:
        gt = put(genestxt, '~/uploads/')[0]

    if gi_taxid is None:
        gi_taxid = taxid

    with cd(env.dir), prefix('source {0}/bin/activate'.format(env.virt_env)):
        if genestxt is not None:
            run('python manage.py genes_load_geneinfo --geneinfo_file={0} --genestxt_file={1} --tax_id={2} --gi_tax_id={3} --symbol_col={4} --systematic_col={5} --alias_col={6} --unique_xrdb={7}'.format(gi, gt, taxid, gi_taxid, symbol, systematic, alias, uniquexrdb))
        else:
            run('python manage.py genes_load_geneinfo --geneinfo_file={0} --tax_id={1} --gi_tax_id={2} --symbol_col={3} --systematic_col={4} --alias_col={5} --unique_xrdb={6}'.format(gi, taxid, gi_taxid, symbol, systematic, alias, uniquexrdb))


@task
def update_haystack_indexes(app_name=None):
    """
    Task that only runs update_haystack_indexes
    """
    env.dir = PROD_CFG['dir']
    env.virt_env = PROD_CFG['virt_env']
    with cd(env.dir), prefix('source {0}/bin/activate'.format(env.virt_env)):
        execute(_update_search_indexes(app_name))
