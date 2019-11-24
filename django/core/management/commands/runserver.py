import errno
import os
import re
import socket
import sys
from datetime import datetime
import django

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.servers.basehttp import (
    WSGIServer, get_internal_wsgi_application, run,
)
from django.utils import autoreload

naiveip_re = re.compile(r"""^(?:
(?P<addr>
    (?P<ipv4>\d{1,3}(?:\.\d{1,3}){3}) |         # IPv4 address
    (?P<ipv6>\[[a-fA-F0-9:]+\]) |               # IPv6 address
    (?P<fqdn>[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*) # FQDN
):)?(?P<port>\d+)$""", re.X)


class Command(BaseCommand):
    help = "Starts a lightweight Web server for development."

    # Validation is called explicitly each time the server is reloaded.
    requires_system_checks = False
    stealth_options = ('shutdown_message',)

    default_addr = '127.0.0.1'
    default_addr_ipv6 = '::1'
    default_port = '8000'
    protocol = 'http'
    server_cls = WSGIServer

    def add_arguments(self, parser):
        # 可选端口号，或ipaddr:port
        parser.add_argument(
            'addrport', nargs='?',
            help='Optional port number, or ipaddr:port'
        )
        parser.add_argument(
            '--ipv6', '-6', action='store_true', dest='use_ipv6',
            help='Tells Django to use an IPv6 address.',
        )
        # 告诉Django不要使用线程
        parser.add_argument(
            '--nothreading', action='store_false', dest='use_threading',
            help='Tells Django to NOT use threading.',
        )
        # 告诉Django不要使用自动加载程序
        parser.add_argument(
            '--noreload', action='store_false', dest='use_reloader',
            help='Tells Django to NOT use the auto-reloader.',
        )

    def execute(self, *args, **options):
        if options['no_color']: # False
            # We rely on the environment because it's currently the only
            # way to reach WSGIRequestHandler. This seems an acceptable
            # compromise considering `runserver` runs indefinitely.
            os.environ["DJANGO_COLORS"] = "nocolor"
        super().execute(*args, **options)

    def get_handler(self, *args, **options):
        """Return the default WSGI handler for the runner."""

        return get_internal_wsgi_application()  #  返回了 wsgi.py 中的 application 对象

    def handle(self, *args, **options):
        if not settings.DEBUG and not settings.ALLOWED_HOSTS:
            raise CommandError('You must set settings.ALLOWED_HOSTS if DEBUG is False.')

        self.use_ipv6 = options['use_ipv6']
        if self.use_ipv6 and not socket.has_ipv6:
            raise CommandError('Your Python does not support IPv6.')
        self._raw_ipv6 = False
        if not options['addrport']:  # False
            self.addr = ''
            self.port = self.default_port
        else:         # 执行
            m = re.match(naiveip_re, options['addrport'])  #  正则 匹配 ip 和  port
            if m is None:
                raise CommandError('"%s" is not a valid port number '
                                   'or address:port pair.' % options['addrport'])
            self.addr, _ipv4, _ipv6, _fqdn, self.port = m.groups()
            """
            '0.0.0.0', '0.0.0.0', None, None, '9999'
            """
            if not self.port.isdigit():
                raise CommandError("%r is not a valid port number." % self.port)
            if self.addr:
                if _ipv6:
                    self.addr = self.addr[1:-1]
                    self.use_ipv6 = True
                    self._raw_ipv6 = True
                elif self.use_ipv6 and not _fqdn:
                    raise CommandError('"%s" is not a valid IPv6 address.' % self.addr)
        if not self.addr:
            self.addr = self.default_addr_ipv6 if self.use_ipv6 else self.default_addr
            self._raw_ipv6 = self.use_ipv6
        self.run(**options)          # 关键代码, 到下方 方法

    def run(self, **options):
        # 运行服务器，如果需要使用自动加载程序。."
        """Run the server, using the autoreloader if needed."""
        use_reloader = options['use_reloader']  # True

        if use_reloader:
            # inner_run  为 Django 开启的主线程的 目标回调函数
            # autoreload = django\utils\autoreload.py
            autoreload.run_with_reloader(self.inner_run, **options) # 关键代码
        else:
            self.inner_run(None, **options)

    def inner_run(self, *args, **options):  #  非常重要 的 方法
        """
        self = <django.contrib.staticfiles.management.commands.runserver.Command object at 0x0365E150>
        :param args: ()
        :param options:  为命令解析 结果
        :return:
        """
        # If an exception was silenced in ManagementUtility.execute in order
        # to be raised in the child process, raise it now.
        autoreload.raise_last_exception()  # 作用不理解

        threading = options['use_threading']  # True
        # 'shutdown_message' is a stealth option.
        shutdown_message = options.get('shutdown_message', '')  # ""

        quit_command = 'CTRL-BREAK' if sys.platform == 'win32' else 'CONTROL-C' # "CTRL-BREAK"

        self.stdout.write("Performing system checks...\n\n")
        self.check(display_num_errors=True)          # 不理解
        # Need to check migrations here, so can't use the
        # requires_migrations_check attribute.
        self.check_migrations()                      # 不理解
        now = datetime.now().strftime('%B %d, %Y - %X')
        self.stdout.write(now)
        self.stdout.write((
            "Django version %(version)s, using settings %(settings)r\n"
            "Starting development server at %(protocol)s://%(addr)s:%(port)s/\n"
            "Quit the server with %(quit_command)s.\n"
        ) % {
            "version": self.get_version(),
            "settings": settings.SETTINGS_MODULE,
            "protocol": self.protocol,
            "addr": '[%s]' % self.addr if self._raw_ipv6 else self.addr,
            "port": self.port,
            "quit_command": quit_command,
        })

        try:
            handler = self.get_handler(*args, **options) #  返回了 wsgi.py 中的 application 对象
            # 关键代码
            run(self.addr, int(self.port), handler,      #  开启 wsgi Web  服务
                ipv6=self.use_ipv6, threading=threading, server_cls=self.server_cls)
        except socket.error as e:
            # Use helpful error messages instead of ugly tracebacks.
            ERRORS = {
                errno.EACCES: "You don't have permission to access that port.",
                errno.EADDRINUSE: "That port is already in use.",
                errno.EADDRNOTAVAIL: "That IP address can't be assigned to.",
            }
            try:
                error_text = ERRORS[e.errno]
            except KeyError:
                error_text = e
            self.stderr.write("Error: %s" % error_text)
            # Need to use an OS exit because sys.exit doesn't work in a thread
            os._exit(1)
        except KeyboardInterrupt:
            if shutdown_message:
                self.stdout.write(shutdown_message)
            sys.exit(0)


# Kept for backward compatibility  保持向后兼容性
BaseRunserverCommand = Command
