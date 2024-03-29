from django.apps import AppConfig
from django.contrib.staticfiles.checks import check_finders
from django.core import checks
from django.utils.translation import gettext_lazy as _


class StaticFilesConfig(AppConfig):
    name = 'django.contrib.staticfiles'
    verbose_name = _("Static Files")
    ignore_patterns = ['CVS', '.*', '*~']

    def ready(self):
        """
        check_finders : 为 收集的  错误的 集合 列表 errors = [...]
        """
        checks.register(check_finders, 'staticfiles')
