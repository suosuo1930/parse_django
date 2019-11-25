from urllib.parse import urlparse
from urllib.request import url2pathname

from django.conf import settings
from django.contrib.staticfiles import utils
from django.contrib.staticfiles.views import serve
from django.core.handlers.exception import response_for_exception
from django.core.handlers.wsgi import WSGIHandler, get_path_info

# 关键 类
# Django  专门 用来处理 静态文件的 类
class StaticFilesHandler(WSGIHandler):
    """
        拦截对静态文件目录的调用的WSGI中间件
        由STATIC_URL设置定义，并为这些文件提供服务
    WSGI middleware that intercepts calls to the static files directory, as
    defined by the STATIC_URL setting, and serves those files.
    """
    # May be used to differentiate between handler types (e.g. in a
    # request_finished signal)
    handles_files = True

    def __init__(self, application):
        print("3333333333333333333333333")
        self.application = application
        # self.application =  <django.core.handlers.wsgi.WSGIHandler object at 0x000001AFF81CB8C8>

        self.base_url = urlparse(self.get_base_url())  # 静态文件 url 解析 结果
        # self.base_url ==  ParseResult(scheme='', netloc='', path='/static/', params='', query='', fragment='')

    # 例如
        # base_url = urlparse('http://www.cwi.nl:80/%7Eguido/Python.html')
        # 则 base_url ==  ParseResult(scheme='http', netloc='www.cwi.nl:80', path='/%7Eguido/Python.html',
        #             params='', query='', fragment='')


        super().__init__()

    def load_middleware(self):
        # Middleware are already loaded for self.application; no need to reload
        # them for self.
        pass

    def get_base_url(self):
        utils.check_settings()
        return settings.STATIC_URL

    def _should_handle(self, path):
        """
        Check if the path should be handled. Ignore the path if:
        * the host is provided as part of the base_url
        * the request's path isn't under the media path (or equal)
        """
        return path.startswith(self.base_url[2]) and not self.base_url[1]

    def file_path(self, url):
        """
        Return the relative path to the media file on disk for the given URL.
        """
        relative_url = url[len(self.base_url[2]):]
        return url2pathname(relative_url)

    def serve(self, request):
        """Serve the request path."""
        return serve(request, self.file_path(request.path), insecure=True)

    def get_response(self, request):
        from django.http import Http404

        if self._should_handle(request.path):
            try:
                return self.serve(request)
            except Http404 as e:
                return response_for_exception(request, e)
        return super().get_response(request)

# 关键代码  关键代码   关键代码   关键代码
    def __call__(self, environ, start_response):
        # print("environ==", environ, "start_response==", start_response)
        # for k,v in enumerate(environ.items()):
        #     print("{}---{}=={}".format(k, str(v[0]).lower(), v[1]))


        if not self._should_handle(get_path_info(environ)):  # 执行
            # get_path_info(environ) = "/"
            # 关键代码
            return self.application(environ, start_response)
        return super().__call__(environ, start_response)
