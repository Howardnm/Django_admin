import pytest

from apps.system.models import Dept
from apps.system.services.dept import DeptCycleError, dept_create, dept_move


@pytest.mark.django_db
def test_path_covers_five_levels():
    """ 测试path覆盖五级部门 """
    root = dept_create(name="总公司")
    level2 = dept_create(name="华东", parent=root)
    level3 = dept_create(name="上海", parent=level2)
    level4 = dept_create(name="研发", parent=level3)
    level5 = dept_create(name="后端", parent=level4)

    assert level5.path == (
        f"/{root.id}/{level2.id}/{level3.id}/{level4.id}/{level5.id}/"
    )


@pytest.mark.django_db
def test_move_rewrites_descendant_paths():
    """ 测试移动部门时，子孙部门的path也会被更新 """
    root = dept_create(name="总公司")
    level2 = dept_create(name="华东", parent=root)
    level3 = dept_create(name="上海", parent=level2)
    level4 = dept_create(name="研发", parent=level3)
    level5 = dept_create(name="后端", parent=level4)

    dept_move(dept=level3, parent=root)
    level5.refresh_from_db()

    assert level5.path == f"/{root.id}/{level3.id}/{level4.id}/{level5.id}/"


@pytest.mark.django_db
def test_move_under_descendant_is_rejected():
    """ 测试移动部门到自身或子孙部门下会被拒绝 """
    root = dept_create(name="总公司")
    level2 = dept_create(name="华东", parent=root)
    level3 = dept_create(name="上海", parent=level2)

    with pytest.raises(DeptCycleError):
        dept_move(dept=root, parent=level3)

    root.refresh_from_db()
    assert root.parent_id is None
    assert Dept.objects.filter(path=level3.path).exists()
