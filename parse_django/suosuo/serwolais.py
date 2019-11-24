from rest_framework import serializers



class BookinfoSerializer(serializers.Serializer):
    """ 图书 的 序列化 器 """
    name = serializers.CharField(label='姓名')
    price = serializers.DecimalField(label='价格')



