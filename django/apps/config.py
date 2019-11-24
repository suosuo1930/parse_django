import os
from importlib import import_module

from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import module_has_submodule

MODELS_MODULE_NAME = 'models'


class AppConfig:
    """Class representing a Django application and its configuration."""
    # 表示Django应用程序及其配置的类。

    def __init__(self, app_name, app_module):
        """
        :param app_name:  app 根路径 字符串 ， settings.INSTALLED_APPS 中的设置
        :param app_module: 此 app  模块实例   <module 'django.contrib.admin'>
        """
        # Full Python path to the application e.g. 'django.contrib.auth'.
        self.name = app_name    # 关键代码

        # Root module for the application e.g. <module 'django.contrib.admin'
        # from 'django/contrib/admin/__init__.py'>.
        self.module = app_module  # 关键代码

        # Reference to the Apps registry that holds this AppConfig. Set by the
        # registry when it registers the AppConfig instance.
        self.apps = None

        # The following attributes could be defined at the class level in a
        # subclass, hence the test-and-set pattern.

        # Last component of the Python path to the application e.g. 'admin'.
        # This value must be unique across a Django project.
        if not hasattr(self, 'label'):
            self.label = app_name.rpartition(".")[2]  # 'auth'    关键代码

        # Human-readable name for the application e.g. "Admin".
        if not hasattr(self, 'verbose_name'):
            self.verbose_name = self.label.title()

        # Filesystem path to the application directory e.g.
        # '/path/to/django/contrib/admin'.
        if not hasattr(self, 'path'):
            self.path = self._path_from_module(app_module)    # 关键代码

    # path= 'E:\\ComputerInstallFiles\\PythonAllVersion\\pythonVirtualEnv\\liujiang_Env\\lib\\site-packages\\django\\contrib\\admin'

        # Module containing models e.g. <module 'django.contrib.admin.models'
        # from 'django/contrib/admin/models.py'>. Set by import_models().
        # None if the application doesn't have a models module.
        self.models_module = None   # 关键代码 , 此 app  的 models.py  模块

        # Mapping of lowercase model names to model classes. Initially set to
        # None to prevent accidental access before import_models() runs.
        self.models = None

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.label)

    def _path_from_module(self, module):
        #  module  :  app 模块实例
        """Attempt to determine app's filesystem path from its module."""
        # 尝试从其模块确定app的文件系统路径。
        # See #21874 for extended discussion of the behavior of this method in
        # various cases.
        # Convert paths to list because Python's _NamespacePath doesn't support
        # indexing.
        paths = list(getattr(module, '__path__', []))

        if len(paths) != 1:
            filename = getattr(module, '__file__', None)
            if filename is not None:
                paths = [os.path.dirname(filename)]
            else:
                # For unknown reasons, sometimes the list returned by __path__
                # contains duplicates that must be removed (#25246).
                paths = list(set(paths))
        if len(paths) > 1:
            raise ImproperlyConfigured(
                "The app module %r has multiple filesystem locations (%r); "
                "you must configure this app with an AppConfig subclass "
                "with a 'path' class attribute." % (module, paths))
        elif not paths:
            raise ImproperlyConfigured(
                "The app module %r has no filesystem location, "
                "you must configure this app with an AppConfig subclass "
                "with a 'path' class attribute." % (module,))
        return paths[0]

    @classmethod
    def create(cls, entry):
        """  用 于 创造 AppConfig 类实例 ，并返回
        entry ： 为  settings.INSTALLED_APPS 中的 一个 选项
        Factory that creates an app config from an entry in INSTALLED_APPS.
        """
        try:
            # If import_module succeeds, entry is a path to an app module,
            # which may specify an app config class with default_app_config.
            # Otherwise, entry is a path to an app config class or an error.
        # 如果import_module成功，则entry是应用程序模块的路径，
        # 它可以用default_app_config指定一个app配置类。
        # 否则，entry是应用程序配置类的路径或错误。
            module = import_module(entry)

        except ImportError:
            # Track that importing as an app module failed. If importing as an
            # app config class fails too, we'll trigger the ImportError again.
            module = None

            mod_path, _, cls_name = entry.rpartition('.')

            # Raise the original exception when entry cannot be a path to an
            # app config class.
            if not mod_path:
                raise

        else:
            try:
                # If this works, the app module specifies an app config class.
                # 如果可以，app 模块指定一个 app 配置类。

            # entry 是一个 字符串， 例如： 'django.contrib.auth.apps.AuthConfig'
                entry = module.default_app_config
            # 判断  此 app 的 __init__.py  文件中 是否有 default_app_config 属性
            except AttributeError:
                # Otherwise, it simply uses the default app config class.
                # 此 处  针对  自定义 app
        # 关键代码
                return cls(entry, module)  # 针对  app  不存在 default_app_config 属性

            else:                          # 针对  app  存在 default_app_config 属性
                mod_path, _, cls_name = entry.rpartition('.')
                """
                mod_path :  "django.contrib.auth.apps"
                cls_name :  "AuthConfig"
                """

        # If we're reaching this point, we must attempt to load the app config
        # class located at <mod_path>.<cls_name>
        mod = import_module(mod_path)  # apps 模块 实例
        try:
            # 此处 针对  内置 app
            cls = getattr(mod, cls_name)  # apps 模块中 AuthConfig 类实例
            # 并将 当前的 cls 重新赋值 为了 app 默认的  app 管理类 ， 例如 AuthConfig

        except AttributeError:
            if module is None:
                # If importing as an app module failed, check if the module
                # contains any valid AppConfigs and show them as choices.
                # Otherwise, that error probably contains the most informative
                # traceback, so trigger it again.
                candidates = sorted(
                    repr(name) for name, candidate in mod.__dict__.items()
                    if isinstance(candidate, type) and
                    issubclass(candidate, AppConfig) and
                    candidate is not AppConfig
                )
                if candidates:
                    raise ImproperlyConfigured(
                        "'%s' does not contain a class '%s'. Choices are: %s."
                        % (mod_path, cls_name, ', '.join(candidates))
                    )
                import_module(entry)
            else:
                raise

        # Check for obvious errors. (This check prevents duck typing, but
        # it could be removed if it became a problem in practice.)
        if not issubclass(cls, AppConfig):
            raise ImproperlyConfigured(
                "'%s' isn't a subclass of AppConfig." % entry)

        # Obtain app name here rather than in AppClass.__init__ to keep
        # all error checking for entries in INSTALLED_APPS in one place.
        try:
            app_name = cls.name  #  例如 'django.contrib.auth'
        except AttributeError:
            raise ImproperlyConfigured(
                "'%s' must supply a name attribute." % entry)

        # Ensure app_name points to a valid module.
        try:
            app_module = import_module(app_name)  # app  auth 模块 实例
        except ImportError:
            raise ImproperlyConfigured(
                "Cannot import '%s'. Check that '%s.%s.name' is correct." % (
                    app_name, mod_path, cls_name,
                )
            )
        print("")

        # Entry is a path to an app config class.
        return cls(app_name, app_module)         # 关键代码

    def get_model(self, model_name, require_ready=True):
        """
        Return the model with the given case-insensitive model_name.

        Raise LookupError if no model exists with this name.
        """
        if require_ready:
            self.apps.check_models_ready()
        else:
            self.apps.check_apps_ready()
        try:
            return self.models[model_name.lower()]
        except KeyError:
            raise LookupError(
                "App '%s' doesn't have a '%s' model." % (self.label, model_name))

    # 返回一个可迭代的模型。
    def get_models(self, include_auto_created=False, include_swapped=False):
        """
        Return an iterable of models.

        By default, the following models aren't included:

        - auto-created models for many-to-many relations without
          an explicit intermediate table,
        - models that have been swapped out.

        Set the corresponding keyword argument to True to include such models.
        Keyword arguments aren't documented; they're a private API.
        """
        self.apps.check_models_ready()

        """
self.models = OrderedDict([
            ('permission', <class 'django.contrib.auth.models.Permission'>), 
            ('group_permissions', <class 'django.contrib.auth.models.Group_permissions'>), 
            ('group', <class 'django.contrib.auth.models.Group'>), 
            ('user_groups', <class 'django.contrib.auth.models.User_groups'>), 
            ('user_user_permissions', <class 'django.contrib.auth.models.User_user_permissions'>), 
            ('user', <class 'django.contrib.auth.models.User'>)
        ])
        """


        for model in self.models.values():
            if model._meta.auto_created and not include_auto_created:
                continue
            if model._meta.swapped and not include_swapped:
                continue
            yield model
    # 添加 models 模块实例 到  app  的 配置实例中
    def import_models(self):
        # Dictionary of models for this app, primarily maintained in the
        # 'all_models' attribute of the Apps this AppConfig is attached to.
        # 这个应用程序的模型字典，主要维护在这个AppConfig附加到的应用程序的'all_models'属性中
        # django.shiwei.info(( 'apps.all_models==', self.apps.all_models ))

        # self.all_models = defaultdict(OrderedDict)
        self.models = self.apps.all_models[self.label] # 初始化 ， 键为 self.label, 值为空的 OrderedDict()
        # print("-----label={} , self.models={} ".format(self.label, self.models))
        # 就 contenttype app 的 self.models = OrderedDict([('contenttype', <class 'django.contrib.contenttypes.models.ContentType'>)])
        # 其他的 app  的 self.models =  OrderedDict()

        # 判断 此 app 中 是否有 models.py 模块
        # self.module == 此 app 的 绝对地址 对象
        # self.module== <module 'django.contrib.auth' from 'D:\\SystemInstallFiles\\python_msi\\pythonVirtual_Env\\liujiang_Env\\lib\\site-packages\\django\\contrib\\auth\\__init__.py'>
        if module_has_submodule(self.module, MODELS_MODULE_NAME):
            models_module_name = '%s.%s' % (self.name, MODELS_MODULE_NAME)
            # 例如:  models_module_name = django.contrib.admin.models

            # 导入 此 app  的 models.py  模块
            # < module 'django.contrib.admin.models' from 'D:\\SystemInstallFiles\\python_msi\\pythonVirtual_Env\\liujiang_Env\\lib\\site-packages\\django\\contrib\\admin\\models.py' >
            self.models_module = import_module(models_module_name)  # 关键代码  ,

    def ready(self):
        """
        Override this method in subclasses to run code when Django starts.
        # 在子类中重写此方法，以便在  Django  启动时运行代码。
        """

