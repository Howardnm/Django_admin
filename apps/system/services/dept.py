from django.db import transaction
from django.db.models import F, Value
from django.db.models.functions import Concat

from apps.system.models import Dept


class DeptCycleError(Exception):
    pass


def dept_create(*, name: str, parent: Dept | None = None, sort: int = 0) -> Dept:
    """ 创建部门 """
    with transaction.atomic():
        """ 创建部门, 先创建部门对象，path设置为pending，保存后再更新path """
        dept = Dept.objects.create(name=name, parent=parent, path="pending", sort=sort)
        dept.path = f"{parent.path}{dept.id}/" if parent else f"/{dept.id}/"
        dept.save(update_fields=["path"])
    return dept


def dept_move(*, dept: Dept, parent: Dept | None) -> Dept:
    """ 移动部门 """
    if parent is not None and (parent.id == dept.id or parent.path.startswith(dept.path)):
        raise DeptCycleError("不能移动到自身或子孙部门下")

    old_path = dept.path
    new_path = f"{parent.path}{dept.id}/" if parent else f"/{dept.id}/"
    with transaction.atomic():
        """ 更新所有子部门的path """
        Dept.objects.filter(path__startswith=old_path).update(path=Concat(Value(new_path), F("path")[len(old_path) :]))
        dept.parent = parent
        dept.path = new_path
        dept.save(update_fields=["parent", "path"])
    return dept
