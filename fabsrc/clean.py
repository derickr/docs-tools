import os
import shutil
import time
import logging

from multiprocessing import cpu_count

logger = logging.getLogger(os.path.basename(__file__))

from fabric.api import task

from fabfile.utils.config import lazy_conf
from fabfile.utils.git import get_branch

from fabfile.make import runner

def _rm_rf(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)

@task
def sphinx(builder='html', conf=None):
    "Removes a specific sphinx build and associated artifacts. Defaults to 'html'. "

    conf = lazy_conf(conf)

    root = conf.paths.branch_output

    cleaner([ os.path.join(root, 'doctrees' + '-' + builder),
              os.path.join(root, builder) ] )

    logger.warning('removed all files supporting the {0} build'.format(builder))

@task
def builds(days=14):
    "Cleans all builds older than 'n' number of days. Defaults to 14."

    days = time.time() - 60*60*24 * int(days)

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../build/')) + '/'

    builds = [ path + o for o in os.listdir(path) if os.path.isdir(path + o)]

    conf = lazy_conf()

    for build in builds:
        branch = build.rsplit('/', 1)[1]

        if branch in conf.git.branches.published:
            continue
        elif branch == get_branch():
            continue
        elif branch == 'public':
            continue
        elif os.stat(build).st_mtime < days:
            _rm_rf(build)
            _rm_rf(path + "public/" + branch)
            logger.warning('removed stale build artifact: ' + build)

def cleaner(paths):
    if len(paths) <= cpu_count() + 1:
        workers = len(paths)
    else:
        workers = cpu_count()

    jobs = ( dict(target=path, dependency=None, job=_rm_rf, args=[path]) for path in paths )

    runner(jobs, pool=workers)
