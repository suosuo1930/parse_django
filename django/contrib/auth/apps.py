from django.apps import AppConfig
from django.core import checks
from django.db.models.query_utils import DeferredAttribute
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _

from . import get_user_model
from .checks import check_models_permissions, check_user_model
from .management import create_permissions
from .signals import user_logged_in


class AuthConfig(AppConfig):
    name = 'django.contrib.auth'
    verbose_name = _("Authentication and Authorization")

    def ready(self):
        post_migrate.connect(  #  发送 信号 迁移 数据库 后 触发执行
            create_permissions,
            dispatch_uid="django.contrib.auth.management.create_permissions"
        )

        #  get_user_model() = <class 'django.contrib.auth.models.User'>
        last_login_field = getattr(get_user_model(), 'last_login', None)
        # Register the handler only if UserModel.last_login is a field.

        if isinstance(last_login_field, DeferredAttribute):  # True
            from .models import update_last_login
            # 信号， 在 用户登录 之 后 触发执行 
            user_logged_in.connect(update_last_login, dispatch_uid='update_last_login')

        checks.register(check_user_model, checks.Tags.models) # 不理解
        checks.register(check_models_permissions, checks.Tags.models)  # 不理解


