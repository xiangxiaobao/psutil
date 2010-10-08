#!/usr/bin/env python
#
# $Id$
#

import errno

try:
    from collections import namedtuple
except ImportError:
    from psutil.compat import namedtuple  # python < 2.6

import _psutil_osx
import _psposix
from psutil.error import *

# --- constants

NUM_CPUS = _psutil_osx.get_num_cpus()
TOTAL_PHYMEM = _psutil_osx.get_total_phymem()

# --- functions

def avail_phymem():
    "Return the amount of physical memory available on the system, in bytes."
    return _psutil_osx.get_avail_phymem()

def used_phymem():
    "Return the amount of physical memory currently in use on the system, in bytes."
    return TOTAL_PHYMEM - _psutil_osx.get_avail_phymem()

def total_virtmem():
    "Return the amount of total virtual memory available on the system, in bytes."
    return _psutil_osx.get_total_virtmem()

def avail_virtmem():
    "Return the amount of virtual memory currently in use on the system, in bytes."
    return _psutil_osx.get_avail_virtmem()

def used_virtmem():
    """Return the amount of used memory currently in use on the system, in bytes."""
    return _psutil_osx.get_total_virtmem() - _psutil_osx.get_avail_virtmem()

def get_system_cpu_times():
    """Return a dict representing the following CPU times:
    user, nice, system, idle."""
    values = _psutil_osx.get_system_cpu_times()
    return dict(user=values[0], nice=values[1], system=values[2], idle=values[3])

def get_pid_list():
    """Returns a list of PIDs currently running on the system."""
    return _psutil_osx.get_pid_list()

def pid_exists(pid):
    """Check For the existence of a unix pid."""
    return _psposix.pid_exists(pid)

# --- decorator

def wrap_exceptions(callable):
    """Call callable into a try/except clause so that if an
    OSError EPERM exception is raised we translate it into
    psutil.AccessDenied.
    """
    def wrapper(self, pid, *args, **kwargs):
        try:
            return callable(self, pid, *args, **kwargs)
        except OSError, err:
            if err.errno == errno.ESRCH:
                raise NoSuchProcess(pid, self._process_name)
            if err.errno == errno.EPERM:
                raise AccessDenied(pid, self._process_name)
            raise
    return wrapper


class Impl(object):

    def __init__(self):
        self._process_name = None

    @wrap_exceptions
    def get_process_info(self, pid):
        """Returns a tuple that can be passed to the psutil.ProcessInfo class
        constructor.
        """
        info_tuple = _psutil_osx.get_process_info(pid)
        self._process_name = info_tuple[2]
        return info_tuple

    @wrap_exceptions
    def get_memory_info(self, pid):
        """Return a tuple with the process' RSS and VMS size."""
        rss, vms = _psutil_osx.get_memory_info(pid)
        meminfo = namedtuple('meminfo', 'rss vms')
        return meminfo(rss, vms)

    @wrap_exceptions
    def get_cpu_times(self, pid):
        user, system = _psutil_osx.get_process_cpu_times(pid)
        cputimes = namedtuple('cputimes', 'user system')
        return cputimes(user, system)

    @wrap_exceptions
    def get_process_create_time(self, pid):
        """Return the start time of the process as a number of seconds since
        the epoch."""
        return _psutil_osx.get_process_create_time(pid)

    def get_open_files(self, pid):
        """Return files opened by process by parsing lsof output."""
        return _psposix.LsofParser(pid, self._process_name).get_process_open_files()

    def get_connections(self, pid):
        """Return etwork connections opened by a process as a list of
        namedtuples."""
        return _psposix.LsofParser(pid, self._process_name).get_process_connections()


