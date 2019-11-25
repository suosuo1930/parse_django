"""
HTTP server that implements the Python WSGI protocol (PEP 333, rev 1.21).

Based on wsgiref.simple_server which is part of the standard library since 2.5.

This is a simple server for use in testing or debugging Django apps. It hasn't
been reviewed for security issues. DON'T USE IT FOR PRODUCTION USE!
"""

import logging
import socket
import socketserver
import sys
from wsgiref import simple_server

from django.core.exceptions import ImproperlyConfigured
from django.core.handlers.wsgi import LimitedStream
from django.core.wsgi import get_wsgi_application
from django.utils.module_loading import import_string

__all__ = ('WSGIServer', 'WSGIRequestHandler')

logger = logging.getLogger('django.server')

# 获取  wsgi.py 中的 application 对象
def get_internal_wsgi_application():
    """
    Load and return the WSGI application as configured by the user in
    ``settings.WSGI_APPLICATION``. With the default ``startproject`` layout,
    this will be the ``application`` object in ``projectname/wsgi.py``.

    This function, and the ``WSGI_APPLICATION`` setting itself, are only useful
    for Django's internal server (runserver); external WSGI servers should just
    be configured to point to the correct application object directly.

    If settings.WSGI_APPLICATION is not set (is ``None``), return
    whatever ``django.core.wsgi.get_wsgi_application`` returns.
    """
    from django.conf import settings
    app_path = getattr(settings, 'WSGI_APPLICATION')
    if app_path is None:
        return get_wsgi_application()

    try:
        return import_string(app_path)  #  返回了 wsgi.py 中的 application 对象
    except ImportError as err:
        raise ImproperlyConfigured(
            "WSGI application '%s' could not be loaded; "
            "Error importing module." % app_path
        ) from err


def is_broken_pipe_error():
    exc_type, exc_value = sys.exc_info()[:2]
    return issubclass(exc_type, socket.error) and exc_value.args[0] == 32


class WSGIServer(simple_server.WSGIServer):     #  关键 类
    """BaseHTTPServer that implements the Python WSGI protocol"""
    # 该数据库将实现Python WSGI协议
    request_queue_size = 10
# httpd_cls(server_address, WSGIRequestHandler, ipv6=ipv6)
    def __init__(self, *args, ipv6=False, allow_reuse_address=True, **kwargs):
        if ipv6:  # False
            self.address_family = socket.AF_INET6
        self.allow_reuse_address = allow_reuse_address  # True
        super().__init__(*args, **kwargs)

    def handle_error(self, request, client_address):
        if is_broken_pipe_error():
            logger.info("- Broken pipe from %s\n", client_address)
        else:
            super().handle_error(request, client_address)


class ThreadedWSGIServer(socketserver.ThreadingMixIn, WSGIServer):
    """A threaded version of the WSGIServer"""
    daemon_threads = True


class ServerHandler(simple_server.ServerHandler):
    http_version = '1.1'

    def __init__(self, stdin, stdout, stderr, environ, **kwargs):
        """
        Use a LimitedStream so that unread request data will be ignored at
        the end of the request. WSGIRequest uses a LimitedStream but it
        shouldn't discard the data since the upstream servers usually do this.
        This fix applies only for testserver/runserver.
        """
        try:
            content_length = int(environ.get('CONTENT_LENGTH'))
        except (ValueError, TypeError):
            content_length = 0
        super().__init__(LimitedStream(stdin, content_length), stdout, stderr, environ, **kwargs)

    def cleanup_headers(self):
        super().cleanup_headers()
        # HTTP/1.1 requires support for persistent connections. Send 'close' if
        # the content length is unknown to prevent clients from reusing the
        # connection.
        if 'Content-Length' not in self.headers:
            self.headers['Connection'] = 'close'
        # Mark the connection for closing if it's set as such above or if the
        # application sent the header.
        if self.headers.get('Connection') == 'close':
            self.request_handler.close_connection = True

    def close(self):
        self.get_stdin()._read_limited()
        super().close()

    def handle_error(self):
        # Ignore broken pipe errors, otherwise pass on
        if not is_broken_pipe_error():
            super().handle_error()


class WSGIRequestHandler(simple_server.WSGIRequestHandler):    #  关键 类
    protocol_version = 'HTTP/1.1'

    def address_string(self):
        # Short-circuit parent method to not call socket.getfqdn
        return self.client_address[0]

    def log_message(self, format, *args):
        extra = {
            'request': self.request,
            'server_time': self.log_date_time_string(),
        }
        if args[1][0] == '4':
            # 0x16 = Handshake, 0x03 = SSL 3.0 or TLS 1.x
            if args[0].startswith('\x16\x03'):
                extra['status_code'] = 500
                logger.error(
                    "You're accessing the development server over HTTPS, but "
                    "it only supports HTTP.\n", extra=extra,
                )
                return

        if args[1].isdigit() and len(args[1]) == 3:
            status_code = int(args[1])
            extra['status_code'] = status_code

            if status_code >= 500:
                level = logger.error
            elif status_code >= 400:
                level = logger.warning
            else:
                level = logger.info
        else:
            level = logger.info

        level(format, *args, extra=extra)

    def get_environ(self):
        # Strip all headers with underscores in the name before constructing
        # the WSGI environ. This prevents header-spoofing based on ambiguity
        # between underscores and dashes both normalized to underscores in WSGI
        # env vars. Nginx and Apache 2.4+ both do this as well.
        for k in self.headers:
            if '_' in k:
                del self.headers[k]

        return super().get_environ()

    def handle(self):
        self.close_connection = True
        self.handle_one_request()
        while not self.close_connection:
            self.handle_one_request()  # 关键代码
        try:
            self.connection.shutdown(socket.SHUT_WR)
        except (socket.error, AttributeError):
            pass

    def handle_one_request(self):
        """Copy of WSGIRequestHandler.handle() but with different ServerHandler"""
        self.raw_requestline = self.rfile.readline(65537)
        if len(self.raw_requestline) > 65536:
            self.requestline = ''
            self.request_version = ''
            self.command = ''
            self.send_error(414)
            return

        if not self.parse_request():  # An error code has been sent, just exit
            return

        # 关键代码
        handler = ServerHandler(
            self.rfile, self.wfile, self.get_stderr(), self.get_environ()
        )
        # 关键代码
        handler.request_handler = self      # backpointer for logging & connection closing
        # 关键代码
        handler.run(self.server.get_app())


"""
StaticFilesHandler-----》 <django.contrib.staticfiles.handlers.StaticFilesHandler>
继承
WSGIHandler  ------ 》   <django.core.handlers.wsgi.WSGIHandler>
继承
BaseHandler -------》    <django.core.handlers.base.BaseHandler> 
(终极类)
"""


"""
WSGIServer  -----》  django.core.servers.basehttp.WSGIServer
继承
WSGIServer  ------》第三方 包  wsgiref.simple_server.WSGIServer
"""

# run(self.addr, int(self.port), handler,      #  开启 wsgi Web  服务
#                ipv6=self.use_ipv6, threading=threading, server_cls=self.server_cls)
def run(addr, port, wsgi_handler, ipv6=False, threading=False, server_cls=WSGIServer):
    """  由 命令 实例 的  inner_run() 方法 调用
    :param addr: '0.0.0.0',
    :param port:  9999
    :param threading: True
    :param ipv6 :  False
    :param wsgi_handler:  <django.contrib.staticfiles.handlers.StaticFilesHandler object>
    :param server_cls:  <class 'django.core.servers.basehttp.WSGIServer'>
    """
    print("11111111111111111111111")
    print("wsgi_handler+++++++++", wsgi_handler)
    server_address = (addr, port)
    if threading: # True
        # 关键代码
        httpd_cls = type('WSGIServer', (socketserver.ThreadingMixIn, server_cls), {})
    else:
        httpd_cls = server_cls

    # 关键代码 ,
    # 类似 等于 wsgiref.py 中 make_server(server_address, wsgi_handler)
    httpd = httpd_cls(server_address, WSGIRequestHandler, ipv6=ipv6)
    # httpd : <django.core.servers.basehttp.WSGIServer object>
    if threading:
        # ThreadingMixIn.daemon_threads indicates how threads will behave on an
        # abrupt shutdown; like quitting the server by the user or restarting
        # by the auto-reloader. True means the server will not wait for thread
        # termination before it quits. This will make auto-reloader faster
        # and will prevent the need to kill the server manually if a thread
        # isn't terminating correctly.
        """
        ThreadingMixIn。daemon_threads指示线程的行为方式
        突然关闭;例如由用户退出服务器或由自动加载程序重新启动。True表示服务器在退出之前不会等待线程终止。
        这将使自动加载更快，并将防止需要杀死服务器手动如果一个线程不正确地终止。
        """
        httpd.daemon_threads = True
        
    # 关键代码, 第三方包 wsgiref 中的 方法. 设定 要 服务 的 APP
    httpd.set_app(wsgi_handler)
    print("set  after +++++++++++++++++")
    #  self.application = <django.contrib.staticfiles.handlers.StaticFilesHandler object>

    httpd.serve_forever()  # socket  开启 服务 监听
