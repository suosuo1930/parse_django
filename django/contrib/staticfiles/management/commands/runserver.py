from django.conf import settings
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.management.commands.runserver import (
    Command as RunserverCommand,
)
import django

class Command(RunserverCommand):
    # 启动用于开发的轻量级Web服务器，并提供静态文件。
    help = "Starts a lightweight Web server for development and also serves static files."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        # 告诉Django不要在STATIC_URL中自动提供静态文件。
        parser.add_argument(
            '--nostatic', action="store_false", dest='use_static_handler',
            help='Tells Django to NOT automatically serve static files at STATIC_URL.',
        )
        # 允许服务静态文件，即使调试是错误的
        parser.add_argument(
            '--insecure', action="store_true", dest='insecure_serving',
            help='Allows serving static files even if DEBUG is False.',
        )

    def get_handler(self, *args, **options):
        """
        Return the static files serving handler wrapping the default handler,
        if static files should be served. Otherwise return the default handler.
        """
        handler = super().get_handler(*args, **options)  #  返回了 wsgi.py 中的 application 对象
        use_static_handler = options['use_static_handler']  # True
        insecure_serving = options['insecure_serving']      # False
        if use_static_handler and (settings.DEBUG or insecure_serving):  # True
            return StaticFilesHandler(handler)  # 关键代码
        return handler
