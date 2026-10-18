from rest_framework.response import Response
from rest_framework.views import APIView

from apps.system.api.serializers import IdListSerializer
from apps.system.models import Dept, Menu, Role
from apps.system.selectors.access import users_visible_to
from apps.system.services.assignment import (
    PrivilegeEscalationError,
    assign_role_depts,
    assign_role_menus,
    assign_user_roles,
)


def error(code, message, status):
    """返回错误响应。"""
    return Response({"code": code, "message": message, "errors": {}}, status=status)


def unique_ids(ids):
    """返回唯一的 ID 列表，保持原有顺序。即去除重复的 ID。"""
    return list(dict.fromkeys(ids))


class UserRoleAssignView(APIView):
    """用户角色分配视图。"""
    permission_code = "system:user:assign-role"

    def put(self, request, user_id):
        """
        为指定用户分配角色。
        仅允许分配当前用户可见范围内的角色，且不能分配比当前用户更宽的数据范围的角色。
        """
        target = users_visible_to(user=request.user).filter(id=user_id).first()
        if target is None:
            return error("not_found", "用户不存在", 404)
        serializer = IdListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = unique_ids(serializer.validated_data["ids"])
        roles = list(Role.objects.filter(id__in=ids))
        if len(roles) != len(ids):
            return error("not_found", "角色不存在", 404)
        try:
            assign_user_roles(actor=request.user, user=target, roles=roles)
        except PrivilegeEscalationError as exc:
            return error("privilege_escalation", str(exc), 403)
        return Response({"ids": [role.id for role in roles]})


class RoleMenuAssignView(APIView):
    """角色菜单分配视图。"""
    permission_code = "system:role:assign-menu"

    def put(self, request, role_id):
        """
        为指定角色分配菜单。
        仅允许为自定义数据范围的角色分配菜单。
        """
        role = Role.objects.filter(id=role_id).first()
        if role is None:
            return error("not_found", "角色不存在", 404)
        serializer = IdListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = unique_ids(serializer.validated_data["ids"])
        menus = list(Menu.objects.filter(id__in=ids))
        if len(menus) != len(ids):
            return error("not_found", "菜单不存在", 404)
        try:
            assign_role_menus(actor=request.user, role=role, menus=menus)
        except PrivilegeEscalationError as exc:
            return error("privilege_escalation", str(exc), 403)
        except ValueError as exc:
            return error("invalid_menu", str(exc), 400)
        return Response({"ids": [menu.id for menu in menus]})


class RoleDeptAssignView(APIView):
    """角色部门分配视图。"""
    permission_code = "system:role:assign-dept"

    def put(self, request, role_id):
        """
        为指定角色分配部门。
        仅允许为自定义数据范围的角色分配部门。
        """
        role = Role.objects.filter(id=role_id).first()
        if role is None:
            return error("not_found", "角色不存在", 404)
        serializer = IdListSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = unique_ids(serializer.validated_data["ids"])
        if request.user.scope_depts is None:
            depts = list(Dept.objects.filter(id__in=ids))
        else:
            depts = list(request.user.scope_depts.filter(id__in=ids))
        if len(depts) != len(ids):
            return error("not_found", "部门不存在", 404)
        try:
            assign_role_depts(role=role, depts=depts)
        except ValueError as exc:
            return error("invalid_scope", str(exc), 400)
        return Response({"ids": [dept.id for dept in depts]})
