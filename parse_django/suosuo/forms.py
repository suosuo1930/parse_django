from django import forms

from resi import models


class BookForms(forms.Form):
    name = forms.CharField(max_length=120,
                           min_length=6,
                           widget=forms.TextInput(
                               attrs={
                                   "class": "form-control",
                                   'require': 'require',
                               }
                           ),
                           error_messages={
                               'invaild': '格式不正确',
                               'require': True,
                               'min_length': "最短 6 位"
                           },
                           help_text="书名",
                           required=True,
                           validators={},
                           label='用户名',
                           label_suffix="sss",
                           initial="施伟",
                           )
    price = forms.DecimalField(max_digits=5, decimal_places=2)
    img = forms.CharField(max_length=150,)
    authors = forms.ModelMultipleChoiceField(queryset=models.Author.objects.all(),
                                             widget=forms.Select(attrs={
                                                "background-color": "red",
                                                 "class": 'form-control',
                                             }),
                                             error_messages={
                                                 "invaild": "非法格式",
                                             },
                                             label="出版作者"
                                             )
    def clean_name(self):
        print('name-------------------', self.cleaned_data['name'])
        return self.cleaned_data['name']



    def clean_authors(self):
        print('authors=================', self.cleaned_data['authors'])
        return self.cleaned_data['authors']

    def clean_price(self):
        print('price ============')
        return self.cleaned_data['price']

    def clean(self):
        print("clean --------------------")
        return self.cleaned_data



class BookModleForm(forms.ModelForm):
    class Meta:
        model = models.Book
        fields = "__all__"
        widgets = {
            'name': forms.TextInput(attrs={
                "class": "form-control",
            }),
            "price": forms.NumberInput(attrs={
                "class": "form-control",
            }),
            "img": forms.URLInput(attrs={
                "class": "form-control",
            }),
            "publish": forms.Select(attrs={
                "class": "form-control",
            }),
            "authors": forms.SelectMultiple(attrs={
                'class': "form-control",

            },)

        }
        labels = {
            'name': '用户名',
            'authors': '作者',
            "price": "价格",
            "img": '图片地址',
            'publish':"出版社",
        }
        error_messages = {
            'name': {
                "invaild": '非法',
                'min-length': '不可少于 6 位'
            },
            'authors': {
                'invaild': '非法操作',
            }
        }
        help_texts = {
            'name': 'name help ',
            'authors': 'authors help ',
        }
    def clean_name(self):
        print('name clean ,==', self.cleaned_data['name'])
        return self.cleaned_data['name']

    def clean(self):
        print('全局的 validations')
        return self.cleaned_data

    def clean_authors(self):
        print("authros clean ===", self.cleaned_data['authors'])
        return self.cleaned_data['authors']



