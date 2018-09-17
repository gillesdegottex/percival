'''
Setup a few things first and useful functionsself.
(independent of the ML backend)

Copyright(C) 2017 Engineering Department, University of Cambridge, UK.

License
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
     http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

Author
    Gilles Degottex <gad27@cam.ac.uk>
'''

from __future__ import print_function

import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__))+'/external/pulsemodel/external/pyworld/')

import numpy as np
import random as rn
def numpy_force_random_seed():
    np.random.seed(123) # Replace this line with a "pass" if you want non-deterministic runs
    rn.seed(123)
numpy_force_random_seed()

# Setup a default session
import tensorflow as tf
sess = tf.Session()
sess.__enter__()

import time
import socket
import subprocess
import runpy
# import xml.etree.ElementTree as ET
import defusedxml.ElementTree as ET # safer version

if sys.stdout.isatty():
    try:
        from termcolor import colored
    except:
        def colored(txt, color): return txt
else:
    def colored(txt, color): return txt


def readids(fileids):
    with open(fileids) as f:
        fids = filter(None, [x for x in map(str.strip, f.readlines()) if x])
    return fids


class configuration(object):
    """
    Configuration object that is carried across many functions along the pipeline.
    """

    def __eq__(self, other):
        """Equality test with another configuration object"""
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Inequality test with another configuration object"""
        return not self.__eq__(other)

    def id_train_nb(self):
        """Return the size of the training set (equal or slightly lower than self.id_valid_start)."""
        return self.train_batch_size*int(np.floor(self.id_valid_start/self.train_batch_size))

    def print_content(self):
        """Print the configuration variables"""
        for key in sorted(dir(self)):
            if callable(getattr(self, key)) or key.startswith("__"):
                continue
            if hasattr(self, 'train_hypers'):
                if key in [hyper[0] for hyper in self.train_hypers]:
                    print("    {:<30}{:}    (Attention! hyper-parameter optimized during multi-training)".format(key, getattr(self, key)))
                else:
                    print("    {:<30}{:}".format(key, getattr(self, key)))
            else:
                print("    {:<30}{:}".format(key, getattr(self, key)))
        print('')

    def mergefiles(self, filenames):
        """Merge the content of a configuration file (variables dropped in a Python file) into this configuration object."""
        files_global = dict()
        if isinstance(filenames, list):
            for fname in filenames:
                files_global.update(runpy.run_path(fname))
        else:
            files_global.update(runpy.run_path(filenames))

        for fg in files_global.keys():
            setattr(self, fg, files_global[fg])

    def merge(self, cfgtoadd):
        """Merge the content of configuration object into this one."""
        for k in cfgtoadd.__dict__.keys():
            if k[:2]!='__':
                setattr(self, k, cfgtoadd.__dict__[k])


def print_log(txt, end='\n'):
    """Print txt with a loging format (could use the Python logging system ...))."""
    print(datetime2str()+': '+txt, end=end)
    sys.stdout.flush()

def print_tty(txt, end=''):
    """Print txt only if this is a TTY."""
    if not sys.stdout.isatty():
        return                                              # pragma: no cover

    print_nnl(txt, end=end)

def datetime2str(sec=None):
    """A format of date and time in this pipeline."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(sec))

def time2str(sec=None):
    """A format of time duration in this pipeline (with potential number of days)."""
    nbdays = int(sec/(60*60*24))
    if nbdays>0:
        return str(nbdays)+'d'+time.strftime('%H:%M:%S',time.gmtime(sec))
    else:
        return time.strftime('%H:%M:%S',time.gmtime(sec))

def is_int(v):
    """Return True of v is an integer, False otherwise."""
    # From https://stackoverflow.com/questions/1265665/python-check-if-a-string-represents-an-int-without-using-try-except
    v = str(v).strip()
    return v=='0' or (v if v.find('..') > -1 else v.lstrip('-+').rstrip('0').rstrip('.')).isdigit()


# TODO Likely to be dropped when stop supporting old Python versions
def print_nnl(txt, end=''):
    """Print without new line."""
    print(txt, end=end)
    sys.stdout.flush()

# TODO Likely to be dropped when stop supporting old Python versions
def makedirs(path):
    """Create a directory."""
    import errno
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise                                           # pragma: no cover


# Backend independent functions ------------------------------------------------

def weights_normal_ortho(insiz, outsiz, std, rng, dtype):
    '''
    Orthogonal initialization of weight matrix.

    dtype : theano.config.floatX
    '''
    # Preserve std!
    a = rng.normal(0.0, std, size=(insiz, outsiz))
    u, _, v = np.linalg.svd(a, full_matrices=0)
    if u.shape!=(insiz, outsiz): u=v
    u = u.reshape((insiz, outsiz))
    return np.asarray(u, dtype=dtype)


# System -----------------------------------------------------------------------

def proc_memresident():
    """Return something close to RAM used by the process [MiB]"""
    PID_memsize = subprocess.Popen(['ps', 'h', '-p', str(os.getpid()), '-o', 'rssize'], stdout=subprocess.PIPE).communicate()[0].rstrip()
    if len(PID_memsize)>0:
        return int(PID_memsize)/1024

    return -1                                               # pragma: no cover

def print_sysinfo():
    """Print some information about the system."""
    print_log('System information')
    print('  Working directory: '+os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)))
    print('  PATH:')
    env_PATHs = str(os.getenv('PATH'))
    if env_PATHs:
        env_PATHs = env_PATHs.split(':')
        for p in env_PATHs:
            if len(p)>0: print('      '+p)
    print('  CPATH:')
    env_CPATHs = str(os.getenv('CPATH'))
    if env_CPATHs:
        env_CPATHs = env_CPATHs.split(':')
        for p in env_CPATHs:
            if len(p)>0: print('      '+p)
    print('  LIBRARY_PATH:')
    env_LIBRARY_PATHs = str(os.getenv('LIBRARY_PATH'))
    if env_LIBRARY_PATHs:
        env_LIBRARY_PATHs = env_LIBRARY_PATHs.split(':')
        for p in env_LIBRARY_PATHs:
            if len(p)>0: print('      '+p)
    print('  LD_LIBRARY_PATH:')
    env_LD_LIBRARY_PATHs = str(os.getenv('LD_LIBRARY_PATH'))
    if env_LD_LIBRARY_PATHs:
        env_LD_LIBRARY_PATHs = env_LD_LIBRARY_PATHs.split(':')
        for p in env_LD_LIBRARY_PATHs:
            if len(p)>0: print('      '+p)
    print('  Python executable: '+sys.executable)
    print('  Python version: '+sys.version.replace('\n',''))
    print('    PYTHONPATH:')
    env_PYTHONPATHs = str(os.getenv('PYTHONPATH'))
    if env_PYTHONPATHs:
        env_PYTHONPATHs = env_PYTHONPATHs.split(':')
        for p in env_PYTHONPATHs:
            if len(p)>0:
                print('      '+p)
    print('  Numpy: {} {}'.format(np.version.version, np.__file__))

    # Check for the presence of git
    codedir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    diropts = ['--git-dir={}/.git'.format(codedir), '--work-tree={}'.format(codedir)]
    ret = os.system('git {} {} status > /dev/null 2>&1'.format(diropts[0], diropts[1]))
    if ret!=0:
        print('  Git: No repository detected')              # pragma: no cover
    else:
        print('  Git is available in the working directory:')
        git_describe = subprocess.Popen(['git', diropts[0], diropts[1], 'describe', '--tags', '--always'], stdout=subprocess.PIPE).communicate()[0][:-1]
        print('    Code version: '+git_describe)
        git_branch = subprocess.Popen(['git', diropts[0], diropts[1], 'rev-parse', '--abbrev-ref', 'HEAD'], stdout=subprocess.PIPE).communicate()[0][:-1]
        print('    branch: '+git_branch)
        git_diff = subprocess.Popen(['git', diropts[0], diropts[1], 'diff'], stdout=subprocess.PIPE).communicate()[0] #, '--name-status'
        #git_diff = git_diff.replace('\t',' ').split('\n')
        if len(git_diff)==0:
            print('    current diff: None')                 # pragma: no cover
        else:
            print('    current diff in git.diff file')
            ret = os.system('git {} {} diff > git.diff'.format(diropts[0], diropts[1]))

    print('  HOSTNAME: '+socket.getfqdn())
    print('  USER: '+str(os.getenv('USER')))
    print('  PID: '+str(os.getpid()))
    PBS_JOBID = str(os.getenv('PBS_JOBID'))
    if PBS_JOBID:
        print('  PBS_JOBID: '+PBS_JOBID)                    # pragma: no cover

    print('')

def nvidia_smi_current_gpu():                               # pragma: no cover
    """Returns GPU ID used by the process.

    (tested locally, cannot be tested on Travis CI bcs no GPU available)

    Returns
    -------
    int
        [MiB]
    """

    # if theano.config.device=='cpu': return -2

    try:
        xml = subprocess.Popen(['nvidia-smi', '-q', '-x'], stdout=subprocess.PIPE).communicate()[0]
        root = ET.fromstring(xml)
        for gpu in root.findall('gpu'):
            for proc in gpu.find('processes').findall('process_info'):
                if int(proc.find('pid').text) == os.getpid():
                    return int(gpu.find('minor_number').text)
    except:
        return -1
    return -1

def nvidia_smi_gpu_memused():                               # pragma: no cover
    """Returns the GPU memory used by the process.

    (tested locally, cannot be tested on Travis CI bcs no GPU available)

    Returns
    -------
    int
        [MiB]
    """

    # if theano.config.device=='cpu': return -2

    try:
        xml = subprocess.Popen(['nvidia-smi', '-q', '-x'], stdout=subprocess.PIPE).communicate()[0]
        root = ET.fromstring(xml)
        for gpu in root.findall('gpu'):
            for proc in gpu.find('processes').findall('process_info'):
                if int(proc.find('pid').text) == os.getpid():
                    return int(proc.find('used_memory').text.split(' ')[0])
    except:
        return -1
    return -1

# Logging plot functions -------------------------------------------------------

def log_plot_costs(costs, worst_val, fname, epochs_modelssaved):
    """
    Plot cost functions.

    Parameters
    ----------
    costs : dict
        A dictionary of cost functions. Each entry will be ploted on the same axis.
    worst_val : float
        Worst/Upper limit of the costs values (mainly useful when using LSE).

    fname : str
        File name to save the plots (e.g. costs.png)
    """
    import matplotlib
    matplotlib.use('Agg') # Force matplotlib to not use any Xwindows backend.
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(16, 8), dpi=200)
    plt.title('Cost functions')
    epochs = np.arange(1,1+len(costs[costs.keys()[0]]))
    plt.plot(epochs, worst_val*np.ones(len(epochs)), ':k', label='0-pred')
    for key in sorted(costs.keys()):
        plt.plot(epochs, np.array(costs[key]), label=key)
    if not epochs_modelssaved is None and len(epochs_modelssaved)>0:
        plt.stem(epochs_modelssaved, worst_val*np.ones(len(epochs_modelssaved)), 'gray', markerfmt='.', basefmt=' ')
    plt.xlim([0, len(epochs)])
    plt.xlabel('Epochs')
    # plt.ylim([0.0, 1.1*worst_val])
    plt.ylim([-2.0, 4.0*worst_val])
    plt.ylabel('Cost (RMSE or any loss)')
    plt.legend(loc='lower left')
    plt.grid()
    fig.savefig(fname)
    plt.close()

def log_plot_samples(Y_vals, Y_preds, nbsamples, fname, vocoder, title=''):
    """
    Plot generated samples.
    """
    # Plot predicted/generated data without denormalisation

    import matplotlib
    matplotlib.use('Agg') # Force matplotlib to not use any Xwindows backend.
    import matplotlib.pyplot as plt
    # plt.ion()
    fig = plt.figure(figsize=(nbsamples*12, 24), dpi=200)
    for sidx in xrange(nbsamples):
        # maxidx = np.max(np.where(M[sidx,:]>0))

        ts = np.arange(Y_vals[sidx].shape[0])*vocoder.shift

        plt.subplot(5,nbsamples,1+sidx)
        f0_val = Y_vals[sidx][:,0]
        f0_pred = Y_preds[sidx][:,0]
        plt.plot(ts, f0_val, 'k')
        plt.plot(ts, f0_pred, 'b')
        plt.axis('off')

        SPEC_val = Y_vals[sidx][:,1:1+vocoder.spec_size]
        SPEC_pred = Y_preds[sidx][:,1:1+vocoder.spec_size]
        if vocoder.fs==-1: vocoder.fs=SPEC_val.shape[1]
        plt.subplot(5,nbsamples,nbsamples+1+sidx)
        spec_max = np.max(SPEC_val)
        spec_min = np.min(SPEC_val)
        plt.imshow(SPEC_val.T, origin='lower', aspect='auto', interpolation='none', cmap='jet', extent=[0.0, ts[-1], 0.0, vocoder.fs/2], vmin=spec_min, vmax=spec_max)
        plt.axis('off')
        plt.subplot(5,nbsamples,2*nbsamples+1+sidx)
        plt.imshow(SPEC_pred.T, origin='lower', aspect='auto', interpolation='none', cmap='jet', extent=[0.0, ts[-1], 0.0, vocoder.fs/2], vmin=spec_min, vmax=spec_max)
        plt.axis('off')

        NM_val = Y_vals[sidx][:,1+vocoder.spec_size:]
        NM_pred = Y_preds[sidx][:,1+vocoder.spec_size:]
        plt.subplot(5,nbsamples,3*nbsamples+1+sidx)
        plt.imshow(NM_val.T, origin='lower', aspect='auto', interpolation='none', cmap='gray', extent=[0.0, ts[-1], 0.0, vocoder.fs/2], vmin=0.0, vmax=1.0)  # TODO grey ?
        plt.axis('off')
        plt.subplot(5,nbsamples,4*nbsamples+1+sidx)
        plt.imshow(NM_pred.T, origin='lower', aspect='auto', interpolation='none', cmap='gray', extent=[0.0, ts[-1], 0.0, vocoder.fs/2], vmin=0.0, vmax=1.0)
        plt.axis('off')

    if not title is None: plt.suptitle(title)
    fig.savefig(fname)
    plt.close()
