from rest_framework import serializers

from apps.system.models import DataScope, MenuType, User, UserStatus


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


class UserCreateSerializer(serializers.Serializer):
    """创建用户序列化器。"""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    status = serializers.ChoiceField(choices=UserStatus.choices, required=False, default=UserStatus.ACTIVE)
    dept_id = serializers.IntegerField()


class UserUpdateSerializer(serializers.Serializer):
    """更新用户序列化器。"""
    password = serializers.CharField(write_only=True, required=False)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    status = serializers.ChoiceField(choices=UserStatus.choices)
    dept_id = serializers.IntegerField()


class UserOutSerializer(serializers.Serializer):
    """用户输出序列化器。"""
    id = serializers.IntegerField()
    username = serializers.CharField()
    phone = serializers.CharField()
    status = serializers.CharField()
    dept_id = serializers.IntegerField(allow_null=True)


class RoleSerializer(serializers.Serializer):
    """角色序列化器。"""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=64)
    data_scope = serializers.ChoiceField(choices=DataScope.choices, required=False, default=DataScope.SELF)
    sort = serializers.IntegerField(required=False, min_value=0, default=0)
    is_enabled = serializers.BooleanField(required=False, default=True)


class MenuSerializer(serializers.Serializer):
    """菜单序列化器。"""
    id = serializers.IntegerField(read_only=True)
    parent_id = serializers.IntegerField(allow_null=True)
    name = serializers.CharField(max_length=64)
    type = serializers.ChoiceField(choices=MenuType.choices)
    permission_code = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    route = serializers.CharField(max_length=128, required=False, allow_blank=True, default="")
    sort = serializers.IntegerField(required=False, min_value=0, default=0)
