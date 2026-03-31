from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .models import User
from .serializers import RegisterSerializer, UserSerializer, ChangePasswordSerializer
from .permissions import IsAdmin


class RegisterView(generics.CreateAPIView):
    """
    Public endpoint — anyone can register.
    Creates a new user with the specified role.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Login with email + password.
    Returns access and refresh JWT tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=email, password=password)

        if not user:
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })


class LogoutView(APIView):
    """
    Blacklists the refresh token — user is fully logged out.
    The access token expires naturally after 60 minutes.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {'message': 'Logged out successfully.'},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {'error': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET  — returns the currently logged-in user's profile.
    PATCH — updates their own profile.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': 'Old password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password changed successfully.'})


class UserListView(generics.ListAPIView):
    """
    Admin only — list all users in the system.
    Uses select_related for optimized DB queries.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filterset_fields = ['role', 'is_verified']
    search_fields = ['email', 'first_name', 'last_name', 'national_id']
    ordering_fields = ['created_at', 'last_name']

    def get_queryset(self):
        return User.objects.all().order_by('-created_at')