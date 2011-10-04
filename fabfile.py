"""
Example fabric deploy script that assubmes a Ubuntu (Debian) 
Linux distro. 

"""
import os as _os
from fabric.api import env, run, local, hosts, roles, cd, sudo, put
from fabric.contrib.files import exists
from fabric.decorators import runs_once, with_settings

pyclt1 = 'pyclt1.hackingthought.com'
pyclt2 = 'pyclt2.hackinghtought.com'
pyclt1_priv = '10.179.186.235'
pyclt2_priv = '10.179.186.182'

FLASK_HOSTS = (pyclt1, pyclt2)
NGINX_HOSTS = (pyclt1, pyclt2)
MONGO_HOSTS = (pyclt1, pyclt2)

FLASK_NODES = 'FLASK_NODES'
env.roledefs[FLASK_NODES] = FLASK_HOSTS
env.directory = '/var/ertc'
env.virtual_env_dir = '%s/env' % env.directory
env.activate = 'source %s/bin/activate' % env.virtual_env_dir
env.config_dir = 'config'

def _install_packages(packages):
    """
    Provides a way to abstrac installation based on the linux platform
    """
    run('sudo apt-get install %s' % packages)

def _update_packages():
    run('sudo apt-get update')

def _upgrade_packages():
    _update_packages()
    run('sudo apt-get upgrade')

def build_user():
    """
    Build the remote user and make them a sudoer!!
    """
    # TODO: Get the password from prompt would be really good
    u = env.user # Remember curreent user
    env.user = 'root' # Change user to root temporarily
    if not exists('/home/%s' % u):
        run('adduser --uid 1000 %s' % u)
        # There is lots of command running as sudo so unless you want to type 
        # in the password a log this is key
        run('echo "%s ALL=NOPASSWD: ALL" >> /etc/sudoers' % u) 
    env.user = u


def upload_sshkey():
    """
    Upload ssh keys to make less password typing
    """
    # TODO: support OS X probably use os.env['HOME'] to figure this out
    # and support for dsa ect, probably configuration option would be good
    # for the user and the ssh key
    remote_home = '/home/%s' % env.user
    run('mkdir -p %s/.ssh' % remote_home)
    sudo('chown -R %s %s' % (env.user, remote_home))
    put('~/.ssh/id_rsa.pub', '%s/.ssh/authorized_keys2' % remote_home)


def base_software():
    """
    The basics that make cluster managment a lot easier 
    python - import this
    mercurial - modern SCM that gets out of the way ie great for just getting
    thing done
    git - for checking out dependent libs
    fabric - ehh duh
    supervisor - when you need to run process much easier to do the managment
    when they are custom services like web apps that do not run in the 
    server process like Python, Rails, Java, Golang ect
    gcc - for those quick C tools you need once and a while 
    ed - lots of script want it
    bzip2 - need for doing backups or deployments when they get large
    sysstat - for figuring out io issues
    """
    _upgrade_packages()
    packages = 'python2.7 mercurial fabric gcc ed bzip2 sysstat' +\
            ' python-pip python-virtualenv'
    _install_packages(packages)
    # Supervisor has strange package blow up so doing a little workaround here
    sudo('pip install elementtree') # Have to install it before supervisor will work
    packages = 'supervisor'
    _install_packages(packages)

def bootstrap_server():
    """
    Creates the basic setup for doing things in the future
    """
    build_user()
    upload_sshkey()
    base_software()

def http_software():
    """
    Add all the basic software for httpserves
    """
    base_software()
    packages = 'nginx'
    _install_packages(packages)

def mongo_configure():
    """
    Add configuration to mongo server.
    """
    sudo('echo "replSet = pyclt" >> /etc/mongodb.conf')
def mongo_software():
    """
    Installs the latest version of mongo database (2.0)
    """
    base_software()
    sudo('apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10')
    sudo('echo "deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart' +\
            ' dist 10gen" >> /etc/apt/sources.list')
    sudo('apt-get update')
    packages = 'mongodb-10gen'
    _install_packages(packages)
    mongo_configure()
    sudo('service mongodb restart')

def prepare():
    """
    Make sure deploy directory exists and is owned by
    the env.user
    """
    if not exists(env.directory):
        sudo('mkdir -p %s' % env.directory) 
        sudo('chown -R %s %s' % (env.user, env.directory))

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


def _library_commands():
    """
    Install the libraries needed for the applicaiton
    (This should be run in development)
    """
    commands = []
    libs = ('fabric', 'flask', 'mongokit')
    for l in libs:
        commands.append('pip install %s' % l)

    return commands

def install_libs():
    """
    Installs the dependent libraries in the virtual enviornment 
    on the server
    """
    for c in _library_commands():
        virtual_env(c)

def bootstrap_env():
    """
    Get the entire enviornment setup
    """
    prepare()
    create_env()
    install_libs()

def local_install_libs():
    """
    Installing libraries on developer machines
    """
    for c in _library_commands():
        local(c)

def config_supervisor():
    """
    Copies the supervisord configuration to the server
    """
    put('%s/super_ertc.conf' % env.config_dir, '/tmp/super_ertc.conf')
    sudo('mv /tmp/super_ertc.conf /etc/supervisor/conf.d/ertc.conf')

def config_nginx():
    """
    Copies the nginx configuration to the server
    """
    put('%s/nginx_ertc.conf' % env.config_dir, '/tmp/nginx_ertc.conf')
    sudo('mv /tmp/nginx_ertc.conf /etc/nginx/sites-available/ertc.conf')
    if exists('/etc/nginx/sites-enabled/ertc.conf'):
        sudo('rm /etc/nginx/sites-enabled/ertc.conf')
    sudo('ln -s /etc/nginx/sites-available/ertc.conf /etc/nginx/sites-enabled')

def init_mongo_replication():
    """
    One time initialize mongo server setup
    """
    c = 'cfg = {' +\
            '{_id:"pyclt", members: [{_id:0, host:"%s"}, {_id:1, host:"%s"}]}};' % (pyclt1_priv, pyclt2_priv) +\
            'rs.initiate(cfg);rs.status();db.getMongo().setSlaveOk();'
    run('echo "%s" | mongo' % c)

def restart_flask():
    """
    Restart flask application server
    """
    sudo('service supervisor restart')
    sudo('supervisorctl reload')
    sudo('supervisorctl restart ertc')

def restart_nginx():
    """
    Restart nginx web server
    """
    sudo('service nginx restart')

@runs_once # Don't run per node in the deployment!!
def package_code():
    """
    Export code and ship it up to server. Kinda old school these days.
    Most do some fancy pull from repository directly. For automated 
    test suite I can see the value of that but for deployment not sure
    I follow.
    """
    local('rm -rf /tmp/ertc.tbz2')
    local('git archive master | bzip2 > /tmp/ertc.tbz2')

@roles(FLASK_NODES)
def deploy_code():
    """
    This does the actual shipping of configuraiton and code up to the 
    cluster.
    """
    config_supervisor()
    config_nginx()
    put('config/server.*', env.directory) # Copy up ssh keys
    package_code()
    put('/tmp/ertc.tbz2', '/tmp')
    # Fat atomic shuffling of code 
    if exists('%s/ertc' % env.directory):
        run('mv %s/ertc /tmp/old_ertc' % env.directory)
    run('mkdir -p %s/ertc' % env.directory)
    run('mv /tmp/ertc.tbz2 %s/ertc && cd %s/ertc && tar jxf ertc.tbz2 ' % (env.directory, env.directory) +\
            '&& rm ertc.tbz2 && rm -rf /tmp/old_ertc')
    run('cd /var/ertc/ertc; wget https://raw.github.com/pythonclt/RTC-Python-Wrapper/master/RTC.py;' +\
            'wget https://raw.github.com/pythonclt/RTC-Python-Wrapper/master/RTC_helpers.py')
    restart_flask()
    restart_nginx()
    
    
