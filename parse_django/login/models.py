from django.db import models

# Create your models here.

class User(models.Model):

    gender = (
        ('male', '男'),
        ('female', '女')
    )

    name = models.CharField(max_length=128, unique=True)
    password = models.CharField(max_length=256)
    email = models.EmailField(unique=True)
    sex = models.CharField(max_length=32, choices=gender, default='男')
    c_time = models.DateField(auto_now_add=True)
    has_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-c_time']
        verbose_name = '用户'
        verbose_name_plural = '用户'


class ConfirmString(models.Model):
    code = models.CharField(max_length=256)
    user = models.OneToOneField('User', on_delete=models.CASCADE)
    c_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.name + self.code

    class Meta:
        ordering = ['-c_time']
        verbose_name = '确认码'
        verbose_name_plural = '确认码'



#
# from django.contrib.auth.models import  User
#
#
#
# from django.contrib.auth.models import (
#     BaseUserManager, AbstractBaseUser,PermissionsMixin
# )
#
#
# class MyUserManager(BaseUserManager):
#     def create_user(self, email, name, password=None):
#         """
#         Creates and saves a User with the given email, date of
#         birth and password.
#         """
#         if not email:
#             raise ValueError('Users must have an email address')
#
#         user = self.model(
#             email=self.normalize_email(email),
#             name=name,
#         )
#
#         user.set_password(password)
#         user.save(using=self._db)
#         return user
#
#     def create_superuser(self, email, name, password):
#         """
#         Creates and saves a superuser with the given email, date of
#         birth and password.
#         """
#         user = self.create_user(
#             email,
#             password=password,
#             name=name,
#         )
#         user.is_admin = True
#         user.save(using=self._db)
#         return user
#
#
# class UserProfile(AbstractBaseUser, PermissionsMixin):
#     email = models.EmailField(
#         verbose_name='email address',
#         max_length=255,
#         unique=True,
#         # default="shiwei@qq.com",
#         # blank = True,
#         # null = True,
#     )
#     name = models.CharField(max_length=1024, verbose_name='姓名')
#     # role = models.ManyToManyField('Role', blank=True, null=True, verbose_name='拥有角色')
#     is_active = models.BooleanField(default=True)
#     is_admin = models.BooleanField(default=True)
#     is_staff = models.BooleanField(default=True)
#
#     objects = MyUserManager()
#
#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['name']
#     class Meta:
#         verbose_name_plural = "自定义用户登录表"
#         permissions = (
#             ("repository_backend_page", "可访问所有 app 下的 所有表"),
#             ("repository_app_page", "可访问一个 app 下的所有表"),
#             ("repository_table_obj_list", "可访问一张表中的 所有 数据记录"),
#             ("repository_table_obj_add", "可添加表记录数据"),
#             ("repository_table_obj_change", "可对表记录数据进行修改"),
#             ("repository_table_obj_delete", "可删除表记录数据"),
#         )
#     def get_full_name(self):
#         # The user is identified by their email address
#         return self.email
#
#     def get_short_name(self):
#         # The user is identified by their email address
#         return self.email
#
#     def __str__(self):
#         return self.email

    # def has_perm(self, perm, obj=None):
    #     "Does the user have a specific permission?"
    #     # Simplest possible answer: Yes, always
    #     return True
    #
    # def has_module_perms(self, app_label):
    #     "Does the user have permissions to view the app `app_label`?"
    #     # Simplest possible answer: Yes, always
    #     return True
    #
    # @property
    # def is_staff(self):
    #     "Is the user a member of staff?"
    #     # Simplest possible answer: All admins are staff
    #     return self.is_admin

