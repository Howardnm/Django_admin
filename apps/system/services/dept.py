from django.db import transaction
from django.db.models import F, ProtectedError, Value
from django.db.models.functions import Concat

from apps.system.models import Dept


class DeptCycleError(Exception):
    pass


class DeptInUseError(Exception):
    pass


def dept_create(*, name: str, parent: Dept | None = None, sort: int = 0) -> Dept:
    """
    创建部门。
    如果有父部门，则path为父部门path + 当前部门id + /
    """
    with transaction.atomic():
        """
        1. 创建部门，path先写成pending
        2. 根据父部门path更新path
        """
        dept = Dept.objects.create(name=name, parent=parent, path="pending", sort=sort)
        if parent is None:
            dept.path = f"/{dept.id}/"
        else:
            dept.path = f"{parent.path}{dept.id}/"
        dept.save(update_fields=["path"])
    return dept


def dept_move(*, dept: Dept, parent: Dept | None) -> Dept:
    """
    移动部门。
    如果parent为None，则移动到根部门下。
    """
    if parent is not None and parent.id == dept.id:
        raise DeptCycleError("不能移动到自身或子孙部门下")
    if parent is not None and parent.path.startswith(dept.path):
        raise DeptCycleError("不能移动到自身或子孙部门下")

    old_path = dept.path
    if parent is None:
        new_path = f"/{dept.id}/"
    else:
        new_path = f"{parent.path}{dept.id}/"
    with transaction.atomic():
        """
        1. 更新所有子部门path
        2. 更新当前部门path和parent
        """
        Dept.objects.filter(path__startswith=old_path).update(
            path=Concat(Value(new_path), F("path")[len(old_path) :])
        )
        dept.parent = parent
        dept.path = new_path
        dept.save(update_fields=["parent", "path"])
    return dept


def dept_update(*, dept: Dept, name: str, sort: int, parent: Dept | None) -> Dept:
    """
    更新部门。
    如果父部门发生变化，则调用dept_move移动部门。
    """
    parent_changed = False
    if parent is None and dept.parent_id is not None:
        parent_changed = True
    if parent is not None and parent.id != dept.parent_id:
        parent_changed = True
    if parent_changed:
        dept_move(dept=dept, parent=parent)
        dept.refresh_from_db()
    dept.name = name
    dept.sort = sort
    dept.save(update_fields=["name", "sort"])
    return dept


def dept_delete(*, dept: Dept) -> None:
    """
    删除部门。
    如果部门有子部门或用户，则抛出异常。
    """
    if dept.children.exists():
        raise DeptInUseError("请先删除或移走下级部门")
    if dept.users.exists():
        raise DeptInUseError("部门下还有用户")
    try:
        dept.delete()
    except ProtectedError:
        raise DeptInUseError("部门正在被使用")
