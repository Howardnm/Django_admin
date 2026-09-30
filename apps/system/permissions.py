from rest_framework.permissions import BasePermission

from apps.system.selectors.access import permission_codes_for, scope_depts_for


class HasPermissionCode(BasePermission):
    """
    检查用户是否拥有指定的权限码。
    如果视图没有指定 permission_code 属性，则默认允许访问。
    如果用户是超级用户，则默认允许访问。
    """
    def has_permission(self, request, view):
        code = getattr(view, "permission_code", None)
        if code is None:
            return True
        user = request.user
        if not user.is_authenticated:
            return False
        if not hasattr(user, "permission_codes"):
            user.permission_codes = permission_codes_for(user=user)
            user.scope_depts = scope_depts_for(user=user)
        if user.is_superuser:
            return True
        return code in user.permission_codes