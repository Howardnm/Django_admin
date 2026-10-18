from rest_framework import serializers

from apps.system.models import User


class LoginSerializer(serializers.Serializer):
    """登录序列化器。"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class MeSerializer(serializers.ModelSerializer):
    """获取当前登录用户信息序列化器。"""
    permission_codes = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = User
        fields = ["id", "username", "phone", "status", "dept", "permission_codes"]


class DeptSerializer(serializers.Serializer):
    """部门序列化器。"""
    id = serializers.IntegerField(read_only=True)
    parent_id = serializers.IntegerField(allow_null=True)
    name = serializers.CharField(max_length=64)
    sort = serializers.IntegerField(required=False, min_value=0, default=0)
