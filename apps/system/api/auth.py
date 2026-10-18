from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.system.api.serializers import LoginSerializer, MeSerializer
from apps.system.models import User, UserStatus
from apps.system.selectors.access import permission_codes_for


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            username=serializer.validated_data["username"]
        ).first()
        if user is None or not user.check_password(serializer.validated_data["password"]):
            return Response({"code": "invalid_credentials", "message": "用户名或密码错误", "errors": {}}, status=400)
        if user.status != UserStatus.ACTIVE:
            return Response({"code": "user_disabled", "message": "用户已停用", "errors": {}}, status=400)
        refresh = RefreshToken.for_user(user)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh)})


class RefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            refresh = RefreshToken(request.data.get("refresh", ""))
        except TokenError:
            return Response({"code": "invalid_token", "message": "刷新令牌无效", "errors": {}}, status=401)
        return Response({"access": str(refresh.access_token)})


class LogoutView(APIView):
    def post(self, request):
        try:
            RefreshToken(request.data.get("refresh", "")).blacklist()
        except TokenError:
            return Response({"code": "invalid_token", "message": "刷新令牌无效", "errors": {}}, status=401)
        return Response(status=204)


class MeView(APIView):
    def get(self, request):
        request.user.permission_codes = sorted(permission_codes_for(user=request.user))
        return Response(MeSerializer(request.user).data)
