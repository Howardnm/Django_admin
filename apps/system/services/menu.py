from apps.system.models import Menu, MenuType


class MenuError(Exception):
    """菜单服务异常。"""
    def __init__(self, code, message):
        self.code = code
        self.message = message


def _require_button_code(menu_type: str, permission_code: str) -> None:
    """如果菜单类型是按钮，则必须提供权限码。"""
    if menu_type != MenuType.BUTTON:
        return
    if permission_code == "":
        raise MenuError("button_code_required", "按钮必须有权限码")


def _require_unique_code(permission_code: str, menu_id: int | None) -> None:
    """如果提供了权限码，则必须唯一。"""
    if permission_code == "":
        return
    taken = Menu.objects.filter(permission_code=permission_code)
    if menu_id is not None:
        taken = taken.exclude(id=menu_id)
    if taken.exists():
        raise MenuError("code_taken", "权限码已存在")


def _require_no_cycle(menu: Menu, parent: Menu | None) -> None:
    """确保菜单不会移动到自身或子孙菜单下。"""
    current = parent
    while current is not None:
        if current.id == menu.id:
            raise MenuError("menu_cycle", "不能移动到自身或子孙菜单下")
        current = current.parent


def menu_create(*, name: str, menu_type: str, parent: Menu | None, permission_code: str, route: str, sort: int) -> Menu:
    """创建菜单。"""
    _require_button_code(menu_type, permission_code)
    _require_unique_code(permission_code, None)
    return Menu.objects.create(
        name=name,
        type=menu_type,
        parent=parent,
        permission_code=permission_code,
        route=route,
        sort=sort,
    )


def menu_update(*, menu: Menu, name: str, menu_type: str, parent: Menu | None, permission_code: str, route: str, sort: int) -> Menu:
    """更新菜单。"""
    _require_button_code(menu_type, permission_code)
    _require_unique_code(permission_code, menu.id)
    _require_no_cycle(menu, parent)
    menu.name = name
    menu.type = menu_type
    menu.parent = parent
    menu.permission_code = permission_code
    menu.route = route
    menu.sort = sort
    menu.save()
    return menu


def menu_delete(*, menu: Menu) -> None:
    """删除菜单。"""
    if menu.children.exists():
        raise MenuError("menu_in_use", "请先删除或移走下级菜单")
    if menu.role_menus.exists():
        raise MenuError("menu_in_use", "菜单已分配给角色")
    menu.delete()
