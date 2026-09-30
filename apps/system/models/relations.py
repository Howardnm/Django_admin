from django.db import models


class UserRole(models.Model):
    """ 用户角色关联表，用于控制用户对角色的访问权限 """
    user = models.ForeignKey("system.User",on_delete=models.CASCADE,related_name="user_roles")
    role = models.ForeignKey("system.Role",on_delete=models.CASCADE,related_name="user_roles")

    class Meta:
        db_table = "sys_user_role"
        constraints = [
            models.UniqueConstraint(fields=["user", "role"], name="uniq_user_role"),
        ]


class RoleMenu(models.Model):
    """ 角色菜单关联表，用于控制角色对菜单的访问权限 """
    role = models.ForeignKey("system.Role",on_delete=models.CASCADE,related_name="role_menus")
    menu = models.ForeignKey("system.Menu",on_delete=models.CASCADE,related_name="role_menus")

    class Meta:
        db_table = "sys_role_menu"
        constraints = [
            models.UniqueConstraint(fields=["role", "menu"], name="uniq_role_menu"),
        ]


class RoleDept(models.Model):
    """ 角色部门关联表 ，用于控制角色对部门的访问权限，仅在角色数据范围为自定义部门时生效 """
    role = models.ForeignKey("system.Role",on_delete=models.CASCADE,related_name="role_depts")
    dept = models.ForeignKey("system.Dept",on_delete=models.CASCADE,related_name="role_depts")

    class Meta:
        db_table = "sys_role_dept"
        constraints = [
            models.UniqueConstraint(fields=["role", "dept"], name="uniq_role_dept"),
        ]
