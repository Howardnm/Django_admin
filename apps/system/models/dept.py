from django.db import models


class Dept(models.Model):
    """部门表"""
    name = models.CharField("名称", max_length=64)
    parent = models.ForeignKey("self",null=True,blank=True,on_delete=models.PROTECT,related_name="children",verbose_name="上级部门")
    path = models.CharField("路径", max_length=255, editable=False)
    sort = models.PositiveIntegerField("排序", default=0)

    class Meta:
        db_table = "sys_dept"
        ordering = ["sort", "id"]

    def __str__(self):
        return self.name
