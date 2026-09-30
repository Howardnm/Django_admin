from .dept import Dept
from .menu import Menu, MenuType
from .relations import RoleDept, RoleMenu, UserRole
from .role import DataScope, Role
from .user import User

__all__ = [
    "DataScope",
    "Dept",
    "Menu",
    "MenuType",
    "Role",
    "RoleDept",
    "RoleMenu",
    "User",
    "UserRole",
]
