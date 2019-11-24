from django.contrib import admin

# Register your models here.

from resi import models

@admin.register(models.Book)
class BookView(admin.ModelAdmin):
    list_display = ("id", 'name', 'price', 'img',)


@admin.register(models.Publish)
class PublishView(admin.ModelAdmin):
    list_display = ('id', 'name', 'address')


@admin.register(models.Author)
class AuthorView(admin.ModelAdmin):
    list_display = ('id', 'name', 'age')


@admin.register(models.AuthorDetail)
class AuthorDetailView(admin.ModelAdmin):
    list_display = ('id', 'mobile')

# admin.site.register(models.Book, BookView)


