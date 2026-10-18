from apps.system.models import Menu, MenuType, User


def menus_for(*, user: User) -> list[Menu]:
    """获取用户可访问的菜单列表（不包含按钮类型的菜单）。"""
    if user.is_superuser:
        granted = Menu.objects.exclude(type=MenuType.BUTTON)
    else:
        granted = Menu.objects.filter(
            role_menus__role__user_roles__user=user,
            role_menus__role__is_enabled=True,
        ).exclude(type=MenuType.BUTTON)

    selected = {}
    for menu in granted:
        current = menu
        while current is not None:
            if current.id in selected:
                break
            if current.type == MenuType.BUTTON:
                break
            selected[current.id] = current
            current = current.parent
    return sorted(selected.values(), key=lambda item: (item.sort, item.id))
