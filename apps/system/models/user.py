from django.contrib.auth.models import AbstractUser
from django.db import models



class UserStatus(models.TextChoices):
    """ 用户状态枚举 """
    ACTIVE = "active", "启用"
    DISABLED = "disabled", "停用"


class User(AbstractUser):
    """ 用户模型 """
    phone = models.CharField("手机号", max_length=20, blank=True)
    status = models.CharField("状态",max_length=16,choices=UserStatus,default=UserStatus.ACTIVE)
    dept = models.ForeignKey("system.Dept",null=True,blank=True,on_delete=models.PROTECT,related_name="users",verbose_name="部门")


    class Meta:
        db_table = "sys_user"

    @property
    def is_active(self) -> bool:
        """ 重写is_active属性，返回用户状态是否为启用 """
        return self.status == UserStatus.ACTIVE

    @is_active.setter
    def is_active(self, value: bool):
        """ 重写is_active属性的setter方法，根据传入的布尔值设置用户状态 """
        self.status = UserStatus.ACTIVE if value else UserStatus.DISABLED
