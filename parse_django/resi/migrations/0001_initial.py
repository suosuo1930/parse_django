# Generated by Django 2.2 on 2019-11-18 00:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('age', models.IntegerField()),
            ],
            options={
                'verbose_name': '作者',
                'verbose_name_plural': '作者',
                'db_table': 'author',
            },
        ),
        migrations.CreateModel(
            name='Publish',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('address', models.CharField(max_length=64)),
            ],
            options={
                'verbose_name': '出版社',
                'verbose_name_plural': '出版社',
                'db_table': 'publish',
            },
        ),
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('price', models.DecimalField(decimal_places=2, max_digits=5)),
                ('img', models.CharField(blank=True, max_length=150, null=True)),
                ('authors', models.ManyToManyField(db_constraint=False, null=True, related_name='books', to='resi.Author')),
                ('publish', models.ForeignKey(db_constraint=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='books', to='resi.Publish')),
            ],
            options={
                'verbose_name': '书籍',
                'verbose_name_plural': '书籍',
                'db_table': 'book',
            },
        ),
        migrations.CreateModel(
            name='AuthorDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mobile', models.CharField(max_length=11)),
                ('author', models.OneToOneField(db_constraint=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='detail', to='resi.Author')),
            ],
            options={
                'verbose_name': '作者详情',
                'verbose_name_plural': '作者详情',
                'db_table': 'author_detail',
            },
        ),
    ]
