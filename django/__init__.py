from django.utils.version import get_version


import logging
logging.basicConfig(format='%(message)s', level=20)


VERSION = (2, 2, 0, 'final', 0)

__version__ = get_version(VERSION)


def setup(set_prefix=True):
    """
    Configure the settings (this happens as a side effect of accessing the
    first setting), configure logging and populate the app registry.
    Set the thread-local urlresolvers script prefix if `set_prefix` is True.
        配置设置(这是访问的副作用
        配置日志并填充应用注册表。
        如果' set_prefix '为真，则设置线程本地 rlresolvers 脚本前缀
    """
    from django.apps import apps
    from django.conf import settings
    from django.urls import set_script_prefix
    from django.utils.log import configure_logging

    configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)  # 配置 日志 设置

    if set_prefix:
        #
        # 参数为 '/'
        set_script_prefix(
            '/' if settings.FORCE_SCRIPT_NAME is None else settings.FORCE_SCRIPT_NAME
        )
    apps.populate(settings.INSTALLED_APPS)  # 开始 填充



#       self
shiwei = logging
def SOSO(*args):

    args = list(args)
    cur_dir = args[-1]
    args.pop()
    end_str = "位于: <" + str(cur_dir).split('\\', maxsplit=7)[-1] + ">"

    args.append(end_str.replace('\\', '.'))
    logging.info(args)


