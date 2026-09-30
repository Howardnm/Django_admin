from django.db import models


class DataScope(models.TextChoices):
    """ 数据范围枚举 """
    ALL = "all", "全部"
    DEPT = "dept", "本部门"
    DEPT_AND_CHILD = "dept_and_child", "本部门及以下"
    SELF = "self", "仅本人"
    CUSTOM = "custom", "自定义部门"


class Role(models.Model):
    """ 角色表 """
    name = models.CharField("名称", max_length=64, unique=True)
    data_scope = models.CharField("数据范围",max_length=32,choices=DataScope,default=DataScope.SELF,)
    sort = models.PositiveIntegerField("排序", default=0)
    is_enabled = models.BooleanField("启用", default=True)

    class Meta:
        db_table = "sys_role"
        ordering = ["sort", "id"]

    def __str__(self):
        return self.name
