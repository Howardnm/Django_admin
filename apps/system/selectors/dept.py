from django.db.models import QuerySet
from apps.system.models import Dept, User


def depts_visible_to(*, user: User) -> QuerySet[Dept] | None:
    """获取当前用户可见的部门。"""
    if user.scope_depts is None:
        return Dept.objects.all()
    return user.scope_depts
