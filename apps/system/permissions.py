from rest_framework.permissions import BasePermission

from apps.system.selectors.access import permission_codes_for, scope_depts_for


def code_for(declared, request) -> str | None:
    """获取当前请求方法对应的权限码。"""
    if isinstance(declared, str):
        return declared
    return declared.get(request.method.lower())


class HasPermissionCode(BasePermission):
    """视图没声明权限码时放行。声明了字典但当前方法没有对应码时拒绝。"""
    
    def has_permission(self, request, view) -> bool:
        declared = getattr(view, "permission_code", None)
        if declared is None:
            return True
        code = code_for(declared, request)
        if code is None:
            return False
        user = request.user
        if not user.is_authenticated:
            return False
        if not hasattr(user, "permission_codes"):
            user.permission_codes = permission_codes_for(user=user)
            user.scope_depts = scope_depts_for(user=user)
        if user.is_superuser:
            return True
        return code in user.permission_codes
