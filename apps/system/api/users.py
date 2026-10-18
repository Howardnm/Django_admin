from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import DefaultPagination
from apps.system.api.serializers import UserCreateSerializer, UserOutSerializer, UserUpdateSerializer
from apps.system.models import Dept
from apps.system.selectors.access import users_visible_to
from apps.system.services.user import UserError, user_create, user_delete, user_update


def error(code, message, status):
    """返回错误响应。"""
    return Response({"code": code, "message": message, "errors": {}}, status=status)


def find_dept(user, dept_id):
    """查找部门。"""
    if user.scope_depts is None:
        dept = Dept.objects.filter(id=dept_id).first()
    else:
        dept = user.scope_depts.filter(id=dept_id).first()
    if dept is None:
        return None, error("not_found", "部门不存在", 404)
    return dept, None


def find_user(actor, user_id):
    """查找用户。"""
    found = users_visible_to(user=actor).filter(id=user_id).first()
    if found is None:
        return None, error("not_found", "用户不存在", 404)
    return found, None


class UserCollectionView(APIView):
    """
    用户集合视图。
    GET: 获取用户列表。
    POST: 创建用户。
    """
    permission_code = {
        "get": "system:user:list",
        "post": "system:user:create",
    }

    def get(self, request):
        """
        获取用户列表。
        超级用户可以获取所有用户，普通用户只能获取其数据范围内的用户。
        """
        users = users_visible_to(user=request.user).order_by("id")
        paginator = DefaultPagination()
        page = paginator.paginate_queryset(users, request, view=self)
        return paginator.get_paginated_response(UserOutSerializer(page, many=True).data)

    def post(self, request):
        """
        创建用户。
        超级用户可以创建所有用户，普通用户只能创建其数据范围内的用户。
        """
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dept, failure = find_dept(request.user, serializer.validated_data["dept_id"])
        if failure is not None:
            return failure
        try:
            user = user_create(
                username=serializer.validated_data["username"],
                password=serializer.validated_data["password"],
                phone=serializer.validated_data["phone"],
                status=serializer.validated_data["status"],
                dept=dept,
            )
        except UserError as exc:
            return error(exc.code, exc.message, 400)
        return Response(UserOutSerializer(user).data, status=201)


class UserDetailView(APIView):
    """
    用户详情视图。
    GET: 获取用户详情。
    PUT: 更新用户。
    DELETE: 删除用户。
    """
    permission_code = {
        "get": "system:user:list",
        "put": "system:user:update",
        "delete": "system:user:delete",
    }

    def get(self, request, user_id):
        """
        获取用户详情。
        超级用户可以获取所有用户，普通用户只能获取其数据范围内的用户。
        """
        user, failure = find_user(request.user, user_id)
        if failure is not None:
            return failure
        return Response(UserOutSerializer(user).data)

    def put(self, request, user_id):
        """
        更新用户。
        超级用户可以更新所有用户，普通用户只能更新其数据范围内的用户。
        """
        user, failure = find_user(request.user, user_id)
        if failure is not None:
            return failure
        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dept, failure = find_dept(request.user, serializer.validated_data["dept_id"])
        if failure is not None:
            return failure
        try:
            user = user_update(
                user=user,
                phone=serializer.validated_data["phone"],
                status=serializer.validated_data["status"],
                dept=dept,
                password=serializer.validated_data.get("password"),
            )
        except UserError as exc:
            return error(exc.code, exc.message, 400)
        return Response(UserOutSerializer(user).data)

    def delete(self, request, user_id):
        """
        删除用户。
        超级用户可以删除所有用户，普通用户只能删除其数据范围内的用户。
        """
        user, failure = find_user(request.user, user_id)
        if failure is not None:
            return failure
        try:
            user_delete(actor=request.user, user=user)
        except UserError as exc:
            return error(exc.code, exc.message, 400)
        return Response(status=204)
