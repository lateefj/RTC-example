"""
Example fabric deploy script that assubmes a Ubuntu (Debian) 
Linux distro. 

"""
import os as _os
from fabric.api import env, run, local, hosts, roles, cd
from fabric.contrib.files import exists
from fabric.decorators import runs_once

pyclt1 = 'pyclt1.hackingthought.com'
pyclt2 = 'pyclt2.hackinghtought.com'

FLASK_HOSTS = (pyclt1, pyclt2)
NGINX_HOSTS = (pyclt1, pyclt2)
MONGO_HOSTS = (pyclt1, pyclt2)

env.directory = '/var/ertc'
env.virtual_env_dir = '%s/env' % env.directory
env.activate = 'source %s/bin/activate' % env.virtual_env_dir
env.config_dir = 'config'   
def prepare():
    """
    Make sure deploy directory exists and is owned by
    the env.user
    """
    if not exists(env.directory):
        run('sudo mkdir -p %s' % env.directory) 
        run('sudo chown -R %s %s' % (env.user, env.directory))

def create_env():
    """
    Creates the virtual enviornment
    """
    run('cd %s && virtualenv env' % env.directory)


def virtual_env(command):
    """
    Run command in the virutal enviornent
    """
    prepare()
    with cd(env.directory):
        run('cd %s' % env.directory + ' && ' + env.activate + ' && ' + command)


def install_libraries():
    """
    Install the libraries needed for the applicaiton
    (This should be run in development)
    """
    libs = ('fabric', 'flask', 'mongokit')
    for l in libs:
        virtual_env('pip install %s' % l)

def config_supervisor():
    """
    Copies the supervisord configuration to the server
    """
    put('%s/super_ertc.conf' % env.config_dir, '/tmp/super_ertc.conf')
    sudo('mv /tmp/super_ertc.conf /etc/supervisor/config.d/ertc.conf')

def config_nginx():
    """
    Copies the nginx configuration to the server
    """
    put('%s/nginx_ertc.conf' % env.config_dir, '/tmp/nginx_ertc.conf')
    sudo('mv /tmp/nginx_ertc.conf /etc/nginx/config.d/sites-available/ertc.conf')
    sudo('ln -s /etc/nginx/sites-available/ertc.conf /etc/nginx/config/sites-enabled')

def restart_flask():
    """
    Restart flask application server
    """
    sudo('supervisorctl restart ertc')

def restart_nginx():
    """
    Restart nginx web server
    """
    sudo('service nginx restart')

@runs_once
def package_code():
    """
    Export code and ship it up to server. Kinda old school these days.
    Most do some fancy pull from repository directly. For automated 
    test suite I can see the value of that but for deployment not sure
    I follow.
    """
    local('rm -rf /tmp/ertc')
    local('hg archive /tmp/ertc')
    local('cd /tmp; tar jccf ertc.tbz2 ertc')

@roles(FLASK_HOSTS)
def deploy_code():
    """
    This does the actual shipping of configuraiton and code up to the 
    cluster.
    """
    config_supervisor()
    config_nginx()
    package_code()
    put('/tmp/ertc.tbz2', '/tmp')
    # Fat atomic shuffling of code 
    run('mv %s/ertc /tmp/old_ertc && rm -rf %s/ertc ' % (env.directory, env.directory) +\
            '&& mv /tmp/ertc.tbz2 %s && tar jxf ertc.tbz2 && rm ertc.bz2 ' +\
            '&& rm -rf /tmp/old_ertc')
    restart_flask()
    restart_nginx()
    
    
