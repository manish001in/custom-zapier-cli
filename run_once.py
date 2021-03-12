from subprocess import Popen, PIPE, STDOUT

#Creating virtualenv
proc, _ = Popen("virtualenv --python=/usr/bin/python2 venv", shell=True, stdout=PIPE, stderr=STDOUT, close_fds=True).communicate()

#Activating virtualenv
proc, _ = Popen("source venv/bin/activate", shell=True, stdout=PIPE, stderr=STDOUT, close_fds=True).communicate()

#Installing requirements
proc, _ = Popen("venv/bin/pip install requirements.txt", shell=True, stdout=PIPE, stderr=STDOUT, close_fds=True).communicate()

#Setting up the basic/example database needed
proc, _ = Popen("python setup_db.py", shell=True, stdout=PIPE, stderr=STDOUT, close_fds=True).communicate()

