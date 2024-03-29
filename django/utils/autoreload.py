import functools
import itertools
import logging
import os
import pathlib
import signal
import subprocess
import sys
import threading
import time
import traceback
import weakref
from collections import defaultdict
from pathlib import Path
from types import ModuleType
from zipimport import zipimporter

from django.apps import apps
from django.core.signals import request_finished
from django.dispatch import Signal
from django.utils.functional import cached_property
from django.utils.version import get_version_tuple


# self
import django
autoreload_started = Signal()
file_changed = Signal(providing_args=['file_path', 'kind'])

DJANGO_AUTORELOAD_ENV = 'RUN_MAIN'

logger = logging.getLogger('django.utils.autoreload')

# If an error is raised while importing a file, it's not placed in sys.modules.
# This means that any future modifications aren't caught. Keep a list of these
# file paths to allow watching them in the future.
_error_files = []
_exception = None

try:
    import termios
except ImportError:
    termios = None


try:
    import pywatchman
except ImportError:
    pywatchman = None   # 执行 此句


def check_errors(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        global _exception
        try:
            fn(*args, **kwargs)
        except Exception:
            _exception = sys.exc_info()

            et, ev, tb = _exception

            if getattr(ev, 'filename', None) is None:
                # get the filename from the last item in the stack
                filename = traceback.extract_tb(tb)[-1][0]
            else:
                filename = ev.filename

            if filename not in _error_files:
                _error_files.append(filename)

            raise

    return wrapper


def raise_last_exception():
    global _exception
    if _exception is not None:
        raise _exception[0](_exception[1]).with_traceback(_exception[2])


def ensure_echo_on():

    if termios:  # None
        fd = sys.stdin
        if fd.isatty():
            attr_list = termios.tcgetattr(fd)
            if not attr_list[3] & termios.ECHO:
                attr_list[3] |= termios.ECHO
                if hasattr(signal, 'SIGTTOU'):
                    old_handler = signal.signal(signal.SIGTTOU, signal.SIG_IGN)
                else:
                    old_handler = None
                termios.tcsetattr(fd, termios.TCSANOW, attr_list)
                if old_handler is not None:
                    signal.signal(signal.SIGTTOU, old_handler)


def iter_all_python_module_files():
    # This is a hot path during reloading. Create a stable sorted list of
    # modules based on the module name and pass it to iter_modules_and_files().
    # This ensures cached results are returned in the usual case that modules
    # aren't loaded on the fly.
    """
    这是重新加载期间的热路径。根据模块名创建一个稳定排序的模块列表，并将其传递给iter_modules_and_files()。
        这确保了缓存结果在通常情况下不会动态加载模块时返回
    :return:
    """

    # ['sys.modules.items()=', dict_items([('sys', < module 'sys' (built- in) >),
    # ('builtins', < module 'builtins' (built- in) >),
    # ('_frozen_importlib',< module 'importlib._bootstrap' (frozen) >),
    # ('_imp',< module '_imp' (built- in) >),
    # ('_thread', < module '_thread' (built- in) >),
    # ('_warnings', < module '_warnings' (built- in) >),
    # ('_weakref', < module '_weakref' (built- in) >),
    # ('zipimport', < module 'zipimport' (built- in) >),
    # ('_frozen_importlib_external', < module 'importlib._bootstrap_external' (frozen) >),
    # .............................

    modules_view = sorted(list(sys.modules.items()), key=lambda i: i[0])

    modules = tuple(m[1] for m in modules_view if not isinstance(m[1], weakref.ProxyTypes))

    return iter_modules_and_files(modules, frozenset(_error_files))


@functools.lru_cache(maxsize=1)
def iter_modules_and_files(modules, extra_files):
    """Iterate through all modules needed to be watched."""
    # 遍历所有需要监视的模块。
    sys_file_paths = []
    for module in modules:
        # During debugging (with PyDev) the 'typing.io' and 'typing.re' objects
        # are added to sys.modules, however they are types not modules and so
        # cause issues here.
        if not isinstance(module, ModuleType) or getattr(module, '__spec__', None) is None:
            continue
        spec = module.__spec__
        # Modules could be loaded from places without a concrete location. If
        # this is the case, skip them.
        if spec.has_location:
            origin = spec.loader.archive if isinstance(spec.loader, zipimporter) else spec.origin
            sys_file_paths.append(origin)

    results = set()
    for filename in itertools.chain(sys_file_paths, extra_files):
        if not filename:
            continue
        path = pathlib.Path(filename)
        if not path.exists():
            # The module could have been removed, don't fail loudly if this
            # is the case.
            continue
        results.add(path.resolve().absolute())
    return frozenset(results)


@functools.lru_cache(maxsize=1)
def common_roots(paths):
    """
    Return a tuple of common roots that are shared between the given paths.
    File system watchers operate on directories and aren't cheap to create.
    Try to find the minimum set of directories to watch that encompass all of
    the files that need to be watched.
    """
    # Inspired from Werkzeug:
    # https://github.com/pallets/werkzeug/blob/7477be2853df70a022d9613e765581b9411c3c39/werkzeug/_reloader.py
    # Create a sorted list of the path components, longest first.
    path_parts = sorted([x.parts for x in paths], key=len, reverse=True)
    tree = {}
    for chunks in path_parts:
        node = tree
        # Add each part of the path to the tree.
        for chunk in chunks:
            node = node.setdefault(chunk, {})
        # Clear the last leaf in the tree.
        node.clear()

    # Turn the tree into a list of Path instances.
    def _walk(node, path):
        for prefix, child in node.items():
            yield from _walk(child, path + (prefix,))
        if not node:
            yield Path(*path)

    return tuple(_walk(tree, ()))


def sys_path_directories():
    """
    Yield absolute directories from sys.path, ignoring entries that don't
    exist.
    """
    for path in sys.path:
        path = Path(path)
        if not path.exists():
            continue
        path = path.resolve().absolute()
        # If the path is a file (like a zip file), watch the parent directory.
        if path.is_file():
            yield path.parent
        else:
            yield path


def get_child_arguments():
    """
    Return the executable. This contains a workaround for Windows if the
    executable is reported to not have the .exe extension which can cause bugs
    on reloading.
    """
    import django.__main__

    args = [sys.executable] + ['-W%s' % o for o in sys.warnoptions]
    if sys.argv[0] == django.__main__.__file__:
        # The server was started with `python -m django runserver`.
        args += ['-m', 'django']
        args += sys.argv[1:]
    else:
        args += sys.argv
    return args


def trigger_reload(filename):
    logger.info('%s changed, reloading.', filename)
    sys.exit(3)


def restart_with_reloader():
    new_environ = {**os.environ, DJANGO_AUTORELOAD_ENV: 'true'}
    args = get_child_arguments()
    while True:
        exit_code = subprocess.call(args, env=new_environ, close_fds=False)
        if exit_code != 3:
            return exit_code


class BaseReloader:
    def __init__(self):
        self.extra_files = set()
        self.directory_globs = defaultdict(set)
        self._stop_condition = threading.Event()

    def watch_dir(self, path, glob):
        path = Path(path)
        if not path.is_absolute():
            raise ValueError('%s must be absolute.' % path)
        logger.debug('Watching dir %s with glob %s.', path, glob)
        self.directory_globs[path].add(glob)

    def watch_file(self, path):
        path = Path(path)
        if not path.is_absolute():
            raise ValueError('%s must be absolute.' % path)
        logger.debug('Watching file %s.', path)
        self.extra_files.add(path)

    def watched_files(self, include_globs=True):
        # self == <django.utils.autoreload.StatReloader object at 0x035A52F0>
        """
        Yield all files that need to be watched, including module files and
        files within globs.
        生成所有需要监视的文件，包括模块文件和 文件内的粘稠
        """
        yield from iter_all_python_module_files()
        yield from self.extra_files
        if include_globs:
            for directory, patterns in self.directory_globs.items():
                for pattern in patterns:
                    yield from directory.glob(pattern)

    def wait_for_apps_ready(self, app_reg, django_main_thread):
        """
        Wait until Django reports that the apps have been loaded. If the given
        thread has terminated before the apps are ready, then a SyntaxError or
        other non-recoverable error has been raised. In that case, stop waiting
        for the apps_ready event and continue processing.

        Return True if the thread is alive and the ready event has been
        triggered, or False if the thread is terminated while waiting for the
        event.
        """
        while django_main_thread.is_alive():          #  返回线程是否是活动的
            if app_reg.ready_event.wait(timeout=0.1): #  主线程事件
                return True
        else:
            logger.debug('Main Django thread has terminated before apps are ready.')
            return False

    def run(self, django_main_thread):
        """
        被 django.utils.autoreload.start_django() 方法 中被调用
        :param django_main_thread:  <Thread(Thread-1, started daemon 5996)> wsgi socket  句柄
        :return:
        """
        logger.debug('Waiting for apps ready_event.')
        self.wait_for_apps_ready(apps, django_main_thread)
        from django.urls import get_resolver

        # Prevent a race condition where URL modules aren't loaded when the
        # reloader starts by accessing the urlconf_module property.
        get_resolver().urlconf_module  # 关键代码
        # get_resolver() =  URLResolver(RegexPattern(r'^/'), urlconf)
        # urlconf = settings.ROOT_URLCONF

        logger.debug('Apps ready_event triggered. Sending autoreload_started signal.')
        # 接受 此信号的 语句位于  django\utils\translation\__init__.py ，
        # 接受 信号的 回调函数 为:
        # from django.utils.translation.reloader import watch_for_translation_changes
        autoreload_started.send(sender=self)
        self.run_loop()

    def run_loop(self):
        # self = <django.utils.autoreload.StatReloader object at 0x035A52F0>

        ticker = self.tick()  # 执行 其 子类的 tick()方法 ， 也位于 此模块中
        # ticker = <generator object StatReloader.tick at 0x0350CE30>

        while not self.should_stop:
            try:
                next(ticker)
            except StopIteration:
                break
        self.stop()

    def tick(self):
        """
        This generator is called in a loop from run_loop. It's important that
        the method takes care of pausing or otherwise waiting for a period of
        time. This split between run_loop() and tick() is to improve the
        testability of the reloader implementations by decoupling the work they
        do from the loop.
        """
        raise NotImplementedError('subclasses must implement tick().')

    @classmethod
    def check_availability(cls):
        raise NotImplementedError('subclasses must implement check_availability().')

    def notify_file_changed(self, path):
        results = file_changed.send(sender=self, file_path=path)
        logger.debug('%s notified as changed. Signal results: %s.', path, results)
        if not any(res[1] for res in results):
            trigger_reload(path)

    # These are primarily used for testing.
    @property
    def should_stop(self):
        return self._stop_condition.is_set()

    def stop(self):
        self._stop_condition.set()


class StatReloader(BaseReloader):
    SLEEP_TIME = 1  # Check for changes once per second.

    def tick(self):
        # self == <django.utils.autoreload.StatReloader object at 0x035312F0>
        state, previous_timestamp = {}, time.time()
        while True:
            state.update(self.loop_files(state, previous_timestamp))
            previous_timestamp = time.time()
            time.sleep(self.SLEEP_TIME)
            yield

    def loop_files(self, previous_times, previous_timestamp):
        updated_times = {}
        for path, mtime in self.snapshot_files():
            previous_time = previous_times.get(path)
            # If there are overlapping globs, a file may be iterated twice.
            if path in updated_times:
                continue
            # A new file has been detected. This could happen due to it being
            # imported at runtime and only being polled now, or because the
            # file was just created. Compare the file's mtime to the
            # previous_timestamp and send a notification if it was created
            # since the last poll.
            is_newly_created = previous_time is None and mtime > previous_timestamp
            is_changed = previous_time is not None and previous_time != mtime
            if is_newly_created or is_changed:
                logger.debug('File %s. is_changed: %s, is_new: %s', path, is_changed, is_newly_created)
                logger.debug('File %s previous mtime: %s, current mtime: %s', path, previous_time, mtime)
                self.notify_file_changed(path)
                updated_times[path] = mtime
        return updated_times

    def snapshot_files(self):
        for file in self.watched_files(): # 再 执行 父类的  watched_files() 方法
            try:
                mtime = file.stat().st_mtime
            except OSError:
                # This is thrown when the file does not exist.
                continue
            yield file, mtime

    @classmethod
    def check_availability(cls):
        return True


class WatchmanUnavailable(RuntimeError):
    pass


class WatchmanReloader(BaseReloader):
    def __init__(self):
        self.roots = defaultdict(set)
        self.processed_request = threading.Event()
        super().__init__()

    @cached_property
    def client(self):
        return pywatchman.client()

    def _watch_root(self, root):
        # In practice this shouldn't occur, however, it's possible that a
        # directory that doesn't exist yet is being watched. If it's outside of
        # sys.path then this will end up a new root. How to handle this isn't
        # clear: Not adding the root will likely break when subscribing to the
        # changes, however, as this is currently an internal API,  no files
        # will be being watched outside of sys.path. Fixing this by checking
        # inside watch_glob() and watch_dir() is expensive, instead this could
        # could fall back to the StatReloader if this case is detected? For
        # now, watching its parent, if possible, is sufficient.
        if not root.exists():
            if not root.parent.exists():
                logger.warning('Unable to watch root dir %s as neither it or its parent exist.', root)
                return
            root = root.parent
        result = self.client.query('watch-project', str(root.absolute()))
        if 'warning' in result:
            logger.warning('Watchman warning: %s', result['warning'])
        logger.debug('Watchman watch-project result: %s', result)
        return result['watch'], result.get('relative_path')

    @functools.lru_cache()
    def _get_clock(self, root):
        return self.client.query('clock', root)['clock']

    def _subscribe(self, directory, name, expression):
        root, rel_path = self._watch_root(directory)
        query = {
            'expression': expression,
            'fields': ['name'],
            'since': self._get_clock(root),
            'dedup_results': True,
        }
        if rel_path:
            query['relative_root'] = rel_path
        logger.debug('Issuing watchman subscription %s, for root %s. Query: %s', name, root, query)
        self.client.query('subscribe', root, name, query)

    def _subscribe_dir(self, directory, filenames):
        if not directory.exists():
            if not directory.parent.exists():
                logger.warning('Unable to watch directory %s as neither it or its parent exist.', directory)
                return
            prefix = 'files-parent-%s' % directory.name
            filenames = ['%s/%s' % (directory.name, filename) for filename in filenames]
            directory = directory.parent
            expression = ['name', filenames, 'wholename']
        else:
            prefix = 'files'
            expression = ['name', filenames]
        self._subscribe(directory, '%s:%s' % (prefix, directory), expression)

    def _watch_glob(self, directory, patterns):
        """
        Watch a directory with a specific glob. If the directory doesn't yet
        exist, attempt to watch the parent directory and amend the patterns to
        include this. It's important this method isn't called more than one per
        directory when updating all subscriptions. Subsequent calls will
        overwrite the named subscription, so it must include all possible glob
        expressions.
        """
        prefix = 'glob'
        if not directory.exists():
            if not directory.parent.exists():
                logger.warning('Unable to watch directory %s as neither it or its parent exist.', directory)
                return
            prefix = 'glob-parent-%s' % directory.name
            patterns = ['%s/%s' % (directory.name, pattern) for pattern in patterns]
            directory = directory.parent

        expression = ['anyof']
        for pattern in patterns:
            expression.append(['match', pattern, 'wholename'])
        self._subscribe(directory, '%s:%s' % (prefix, directory), expression)

    def watched_roots(self, watched_files):
        extra_directories = self.directory_globs.keys()
        watched_file_dirs = [f.parent for f in watched_files]
        sys_paths = list(sys_path_directories())
        return frozenset((*extra_directories, *watched_file_dirs, *sys_paths))

    def _update_watches(self):
        watched_files = list(self.watched_files(include_globs=False))
        found_roots = common_roots(self.watched_roots(watched_files))
        logger.debug('Watching %s files', len(watched_files))
        logger.debug('Found common roots: %s', found_roots)
        # Setup initial roots for performance, shortest roots first.
        for root in sorted(found_roots):
            self._watch_root(root)
        for directory, patterns in self.directory_globs.items():
            self._watch_glob(directory, patterns)
        # Group sorted watched_files by their parent directory.
        sorted_files = sorted(watched_files, key=lambda p: p.parent)
        for directory, group in itertools.groupby(sorted_files, key=lambda p: p.parent):
            # These paths need to be relative to the parent directory.
            self._subscribe_dir(directory, [str(p.relative_to(directory)) for p in group])

    def update_watches(self):
        try:
            self._update_watches()
        except Exception as ex:
            # If the service is still available, raise the original exception.
            if self.check_server_status(ex):
                raise

    def _check_subscription(self, sub):
        subscription = self.client.getSubscription(sub)
        if not subscription:
            return
        logger.debug('Watchman subscription %s has results.', sub)
        for result in subscription:
            # When using watch-project, it's not simple to get the relative
            # directory without storing some specific state. Store the full
            # path to the directory in the subscription name, prefixed by its
            # type (glob, files).
            root_directory = Path(result['subscription'].split(':', 1)[1])
            logger.debug('Found root directory %s', root_directory)
            for file in result.get('files', []):
                self.notify_file_changed(root_directory / file)

    def request_processed(self, **kwargs):
        logger.debug('Request processed. Setting update_watches event.')
        self.processed_request.set()

    def tick(self):
        request_finished.connect(self.request_processed)
        self.update_watches()
        while True:
            if self.processed_request.is_set():
                self.update_watches()
                self.processed_request.clear()
            try:
                self.client.receive()
            except pywatchman.WatchmanError as ex:
                self.check_server_status(ex)
            else:
                for sub in list(self.client.subs.keys()):
                    self._check_subscription(sub)
            yield

    def stop(self):
        self.client.close()
        super().stop()

    def check_server_status(self, inner_ex=None):
        """Return True if the server is available."""
        try:
            self.client.query('version')
        except Exception:
            raise WatchmanUnavailable(str(inner_ex)) from inner_ex
        return True

    @classmethod
    def check_availability(cls):

        if not pywatchman:  # pywatchman = None

            raise WatchmanUnavailable('pywatchman not installed.')

        client = pywatchman.client(timeout=0.01)
        try:
            result = client.capabilityCheck()
        except Exception:
            # The service is down?
            raise WatchmanUnavailable('Cannot connect to the watchman service.')
        version = get_version_tuple(result['version'])
        # Watchman 4.9 includes multiple improvements to watching project
        # directories as well as case insensitive filesystems.
        logger.debug('Watchman version %s', version)
        if version < (4, 9):
            raise WatchmanUnavailable('Watchman 4.9 or later is required.')


def get_reloader():
    # 返回最适合此环境的重新加载程序
    """Return the most suitable reloader for this environment."""
    try:
        WatchmanReloader.check_availability()  # 报异常
    except WatchmanUnavailable:
        return StatReloader()       # 执行
    return WatchmanReloader()


def start_django(reloader, main_func, *args, **kwargs):
    """  在这个 方法中 开启服务端为一个单独的线程  和  加载 URL 映射关系表
    main_func = 命令实例的 第一级父类中 的 inner_run 方法 引用
    :param reloader:  <django.utils.autoreload.StatReloader object at 0x03530130>
    :param main_func: <bound method Command.inner_run of <django.contrib.staticfiles.management.commands.runserver.Command object
    :param args:  ()
    :param kwargs:  {.......}   # 为命令解析 结果
    """
    ensure_echo_on()  # 不理解

    main_func = check_errors(main_func)   # 作用不理解
    # 开启 一个 django 主线程， 目标函数 为命令实例 中 inner_run() 方法
    django_main_thread = threading.Thread(target=main_func, args=args, kwargs=kwargs)
    django_main_thread.setDaemon(True)
    django_main_thread.start()                  # 1. 开启 Django 主线程
    # 执行 django\core\management\commands\runserver.inner_run(sefl, *args, **options)  方法

    # django_main_thread = <Thread(Thread-1, started daemon 1564)>
    while not reloader.should_stop:  # 判断 线程事件 是否为 True
        try:
            reloader.run(django_main_thread)    # 2. 加载 URL 映射 关系， 传入 socket 句柄
        except WatchmanUnavailable as ex:
            # It's possible that the watchman service shuts down or otherwise
            # becomes unavailable. In that case, use the StatReloader.
            reloader = StatReloader()
            logger.error('Error connecting to Watchman: %s', ex)
            logger.info('Watching for file changes with %s', reloader.__class__.__name__)


def run_with_reloader(main_func, *args, **kwargs):
    """  在命令实例 的 run()  方法 中 被调用，  继而  在这个方法 中 开启 Django
        main_func = 命令实例的 第一级父类中 的 inner_run 方法 引用
        kwargs = { # 为命令解析 结果
            'verbosity': 1, 'settings': None, 'pythonpath': None,
            'traceback': False, 'no_color': False, 'force_color': False,
            'addrport': '0.0.0.0:9999', 'use_ipv6': False, 'use_threading': True,
            'use_reloader': True, 'use_static_handler': True, 'insecure_serving': False
        }
    """

    signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))
    try:
        if os.environ.get(DJANGO_AUTORELOAD_ENV) == 'true':
            reloader = get_reloader()

        # reloader = <django.utils.autoreload.StatReloader object at 0x035312F0>
        #     <django.utils.autoreload.WatchmanReloader>
            logger.info('Watching for file changes with %s', reloader.__class__.__name__)
            start_django(reloader, main_func, *args, **kwargs)   # 关键代码
            """
            reloader:  <django.utils.autoreload.StatReloader object at 0x03530130>
            main_func: <bound method Command.inner_run of <django.contrib.staticfiles.management.commands.runserver.Command object at 0x03244FF0>>
            args: ()
            kwargs : {'verbosity': 1, 'settings': None, 'pythonpath': None, 'traceback': False, 'no_color': False, 'force_color': False, 'addrport': '0.0.0.0:9999', 'use_ipv6': False, 'use_threading': True, 'use_reloader': True, 'use_static_handler': True, 'insecure_serving': False}
            """
        else:
            exit_code = restart_with_reloader()
            sys.exit(exit_code)
    except KeyboardInterrupt:
        pass
