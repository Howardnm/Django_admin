from django.db import models


class MenuType(models.TextChoices):
    """ 菜单类型 """
    CATALOG = "catalog", "目录"
    MENU = "menu", "菜单"
    BUTTON = "button", "按钮"


class Menu(models.Model):
    """ 菜单表 """
    name = models.CharField("名称", max_length=64)
    type = models.CharField("类型", max_length=16, choices=MenuType)
    parent = models.ForeignKey("self",null=True,blank=True,on_delete=models.PROTECT,related_name="children",verbose_name="上级")
    permission_code = models.CharField("权限码", max_length=64, blank=True, default="")
    route = models.CharField("路由", max_length=128, blank=True, default="")
    sort = models.PositiveIntegerField("排序", default=0)

    class Meta:
        db_table = "sys_menu"
        ordering = ["sort", "id"]

    def __str__(self):
        return self.name
