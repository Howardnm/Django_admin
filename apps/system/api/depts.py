from rest_framework.response import Response
from rest_framework.views import APIView

from apps.system.api.serializers import DeptSerializer
from apps.system.selectors.dept import depts_visible_to
from apps.system.services.dept import (
    DeptCycleError,
    DeptInUseError,
    dept_create,
    dept_delete,
    dept_update,
)

from apps.system.models import Dept


def error(code, message, status) -> Response:
    """返回错误响应"""
    return Response({"code": code, "message": message, "errors": {}}, status=status)


def find_parent(user, parent_id) -> tuple[Dept | None, Response | None]:
    """
    查找父部门。
    如果parent_id为None，则返回None。
    如果parent_id不为None，则查找当前用户可见的部门中是否存在该部门，如果不存在则返回错误。
    """
    if parent_id is None:
        if user.scope_depts is not None:
            return None, error("out_of_scope", "不能在数据范围外创建根部门", 403)
        return None, None
    parent = depts_visible_to(user=user).filter(id=parent_id).first()
    if parent is None:
        return None, error("not_found", "部门不存在", 404)
    return parent, None


class DeptCollectionView(APIView):
    """
    部门集合视图。
    GET: 获取当前用户可见的所有部门
    POST: 创建新部门
    """
    permission_code = {
        "get": "system:dept:list",
        "post": "system:dept:create",
    }

    def get(self, request):
        """
        获取当前用户可见的所有部门。
        如果用户是超级管理员，则返回所有部门。
        """
        depts = depts_visible_to(user=request.user)
        return Response(DeptSerializer(depts, many=True).data)

    def post(self, request):
        """
        创建新部门。
        如果用户是超级管理员，则可以创建根部门。
        如果用户不是超级管理员，则只能在其数据范围内创建部门。
        """
        serializer = DeptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parent, failure = find_parent(request.user, serializer.validated_data["parent_id"])
        if failure is not None:
            return failure
        dept = dept_create(
            name=serializer.validated_data["name"],
            parent=parent,
            sort=serializer.validated_data["sort"],
        )
        return Response(DeptSerializer(dept).data, status=201)


class DeptDetailView(APIView):
    """
    部门详情视图。
    PUT: 更新部门
    DELETE: 删除部门
    """
    permission_code = {
        "put": "system:dept:update",
        "delete": "system:dept:delete",
    }

    def put(self, request, dept_id):
        """
        更新部门。
        如果父部门发生变化，则调用dept_move移动部门。
        如果用户是超级管理员，则可以移动到根部门。
        如果用户不是超级管理员，则只能移动到其数据范围内的部门。
        """
        dept = depts_visible_to(user=request.user).filter(id=dept_id).first()
        if dept is None:
            return error("not_found", "部门不存在", 404)
        serializer = DeptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parent, failure = find_parent(request.user, serializer.validated_data["parent_id"])
        if failure is not None:
            return failure
        try:
            dept = dept_update(
                dept=dept,
                name=serializer.validated_data["name"],
                sort=serializer.validated_data["sort"],
                parent=parent,
            )
        except DeptCycleError as exc:
            return error("dept_cycle", str(exc), 400)
        return Response(DeptSerializer(dept).data)

    def delete(self, request, dept_id):
        """
        删除部门。
        如果用户是超级管理员，则可以删除任何部门。
        如果用户不是超级管理员，则只能删除其数据范围内的部门。
        如果部门有子部门或用户，则抛出异常。
        """
        dept = depts_visible_to(user=request.user).filter(id=dept_id).first()
        if dept is None:
            return error("not_found", "部门不存在", 404)
        try:
            dept_delete(dept=dept)
        except DeptInUseError as exc:
            return error("dept_in_use", str(exc), 400)
        return Response(status=204)
