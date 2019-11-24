from django.db import models

# Create your models here.


# from utils.model import BaseModel
class Book(models.Model):
    name = models.CharField(max_length=64)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    img = models.CharField(max_length=150, blank=True, null=True)
    publish = models.ForeignKey(to='Publish', null=True,
                                related_name='books',
                                db_constraint=False,
                                on_delete=models.CASCADE,
                                )
    authors = models.ManyToManyField(to='Author', null=True,
                                     related_name='books',
                                     db_constraint=False,
                                     )

    @property
    def publish_name(self):
        return self.publish.name

    @property
    def authors_info(self):
        author_list = []
        for author in self.authors.all():
            author_list.append({
                'name': author.name,
                'age': author.age,
                'mobile': author.detail.mobile
            })
        return author_list

    # @property
    # def publish_bac(self):
    #     from . import serializers
    #     data = serializers.PublishModelSerializer(self.publish).data
    #     return data

    class Meta:
        db_table = 'book'
        verbose_name = '书籍'
        verbose_name_plural = verbose_name
        # 联合唯一
        # unique_together = ('name', 'publish')

    def __str__(self):
        return self.name


class Publish(models.Model):
    name = models.CharField(max_length=64)
    address = models.CharField(max_length=64)

    class Meta:
        db_table = 'publish'
        verbose_name = '出版社'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Author(models.Model):
    name = models.CharField(max_length=64)
    age = models.IntegerField()

    @property
    def mobile(self):
        return self.detail.mobile

    class Meta:
        db_table = 'author'
        verbose_name = '作者'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class AuthorDetail(models.Model):
    mobile = models.CharField(max_length=11)
    author = models.OneToOneField(to='Author', null=True,
                                  related_name='detail',
                                  db_constraint=False,
                                  on_delete=models.CASCADE
                                  )

    class Meta:
        db_table = 'author_detail'
        verbose_name = '作者详情'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s的详情' % self.author.name
