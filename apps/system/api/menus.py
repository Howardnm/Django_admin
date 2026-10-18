from rest_framework.response import Response
from rest_framework.views import APIView

from apps.system.api.serializers import MenuSerializer
from apps.system.models import Menu
from apps.system.services.menu import MenuError, menu_create, menu_delete, menu_update


def error(code, message, status):
    """返回错误响应"""
    return Response({"code": code, "message": message, "errors": {}}, status=status)


def find_parent(parent_id):
    """查找上级菜单。"""
    if parent_id is None:
        return None, None
    parent = Menu.objects.filter(id=parent_id).first()
    if parent is None:
        return None, error("not_found", "上级菜单不存在", 404)
    return parent, None


class MenuCollectionView(APIView):
    """
    菜单集合视图。
    GET: 获取菜单列表
    POST: 创建菜单
    """
    permission_code = {
        "get": "system:menu:list",
        "post": "system:menu:create",
    }

    def get(self, request):
        """获取菜单列表。"""
        menus = Menu.objects.all().order_by("sort", "id")
        return Response(MenuSerializer(menus, many=True).data)

    def post(self, request):
        """创建菜单。"""
        serializer = MenuSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parent, failure = find_parent(serializer.validated_data["parent_id"])
        if failure is not None:
            return failure
        try:
            menu = menu_create(
                name=serializer.validated_data["name"],
                menu_type=serializer.validated_data["type"],
                parent=parent,
                permission_code=serializer.validated_data["permission_code"],
                route=serializer.validated_data["route"],
                sort=serializer.validated_data["sort"],
            )
        except MenuError as exc:
            return error(exc.code, exc.message, 400)
        return Response(MenuSerializer(menu).data, status=201)


class MenuDetailView(APIView):
    """
    菜单详情视图。
    GET: 获取菜单详情
    PUT: 更新菜单
    DELETE: 删除菜单
    """
    permission_code = {
        "get": "system:menu:list",
        "put": "system:menu:update",
        "delete": "system:menu:delete",
    }

    def get(self, request, menu_id):
        """获取菜单详情。"""
        menu = Menu.objects.filter(id=menu_id).first()
        if menu is None:
            return error("not_found", "菜单不存在", 404)
        return Response(MenuSerializer(menu).data)

    def put(self, request, menu_id):
        """更新菜单。"""
        menu = Menu.objects.filter(id=menu_id).first()
        if menu is None:
            return error("not_found", "菜单不存在", 404)
        serializer = MenuSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parent, failure = find_parent(serializer.validated_data["parent_id"])
        if failure is not None:
            return failure
        try:
            menu = menu_update(
                menu=menu,
                name=serializer.validated_data["name"],
                menu_type=serializer.validated_data["type"],
                parent=parent,
                permission_code=serializer.validated_data["permission_code"],
                route=serializer.validated_data["route"],
                sort=serializer.validated_data["sort"],
            )
        except MenuError as exc:
            return error(exc.code, exc.message, 400)
        return Response(MenuSerializer(menu).data)

    def delete(self, request, menu_id):
        """删除菜单。"""
        menu = Menu.objects.filter(id=menu_id).first()
        if menu is None:
            return error("not_found", "菜单不存在", 404)
        try:
            menu_delete(menu=menu)
        except MenuError as exc:
            return error(exc.code, exc.message, 400)
        return Response(status=204)
