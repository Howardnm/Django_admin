from rest_framework import serializers

from apps.system.models import User


class LoginSerializer(serializers.Serializer):
    """ 用户登录序列化器 """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class MeSerializer(serializers.ModelSerializer):
    """ 用户个人信息序列化器 """
    permission_codes = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = User
        fields = ["id", "username", "phone", "status", "dept", "permission_codes"]
