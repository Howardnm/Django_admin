from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import DefaultPagination
from apps.system.api.serializers import RoleSerializer
from apps.system.models import Role
from apps.system.services.role import RoleError, role_create, role_delete, role_update


def error(code, message, status):
    """返回错误响应"""
    return Response({"code": code, "message": message, "errors": {}}, status=status)


class RoleCollectionView(APIView):
    """
    角色集合视图
    GET: 获取角色列表
    POST: 创建角色
    """
    permission_code = {
        "get": "system:role:list",
        "post": "system:role:create",
    }

    def get(self, request):
        """获取角色列表。"""
        roles = Role.objects.all().order_by("sort", "id")
        paginator = DefaultPagination()
        page = paginator.paginate_queryset(roles, request, view=self)
        return paginator.get_paginated_response(RoleSerializer(page, many=True).data)

    def post(self, request):
        """创建角色。"""
        serializer = RoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            role = role_create(
                name=serializer.validated_data["name"],
                data_scope=serializer.validated_data["data_scope"],
                sort=serializer.validated_data["sort"],
                is_enabled=serializer.validated_data["is_enabled"],
            )
        except RoleError as exc:
            return error(exc.code, exc.message, 400)
        return Response(RoleSerializer(role).data, status=201)


class RoleDetailView(APIView):
    """
    角色详情视图
    GET: 获取角色详情
    PUT: 更新角色
    DELETE: 删除角色
    """
    permission_code = {
        "get": "system:role:list",
        "put": "system:role:update",
        "delete": "system:role:delete",
    }

    def get(self, request, role_id):
        """获取角色详情。"""
        role = Role.objects.filter(id=role_id).first()
        if role is None:
            return error("not_found", "角色不存在", 404)
        return Response(RoleSerializer(role).data)

    def put(self, request, role_id):
        """更新角色。"""
        role = Role.objects.filter(id=role_id).first()
        if role is None:
            return error("not_found", "角色不存在", 404)
        serializer = RoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            role = role_update(
                role=role,
                name=serializer.validated_data["name"],
                data_scope=serializer.validated_data["data_scope"],
                sort=serializer.validated_data["sort"],
                is_enabled=serializer.validated_data["is_enabled"],
            )
        except RoleError as exc:
            return error(exc.code, exc.message, 400)
        return Response(RoleSerializer(role).data)

    def delete(self, request, role_id):
        """删除角色。"""
        role = Role.objects.filter(id=role_id).first()
        if role is None:
            return error("not_found", "角色不存在", 404)
        try:
            role_delete(role=role)
        except RoleError as exc:
            return error(exc.code, exc.message, 400)
        return Response(status=204)
