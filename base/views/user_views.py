# Django Import 
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework import status

# Rest Framework Import
from rest_framework.decorators import api_view,permission_classes,api_view
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework.response import Response
from rest_framework.serializers import Serializer

# Rest Framework JWT 
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

# Local Import 
from base.models import *
from base.serializers import UserSerializer,UserSerializerWithToken

#Socil Accounts
from allauth.socialaccount.models import SocialAccount
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

import uuid
import hashlib
import random
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.views import APIView

# JWT Views
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
       
        serializer = UserSerializerWithToken(self.user).data

        for k,v in serializer.items():
            data[k] =v

        return data
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.username
        token['message'] = "Hello Proshop"
        # ...

        return token

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# SHOP API
@api_view(['GET'])
def getRoutes(request):
    routes =[
        '/api/products/',
        '/api/products/<id>',
        '/api/users',
        '/api/users/register',
        '/api/users/google-login',
        '/api/users/login',
        '/api/users/profile',
    ]
    return Response(routes)


@api_view(['POST'])
def registerUser(request):
    data = request.data
    try:
        user = User.objects.create(
            first_name = data['name'],
            username = data['email'],
            password = make_password(data['password']),
        )

        serializer = UserSerializerWithToken(user,many=False)
        return Response(serializer.data)
    
    except:
        message = {"detail":"User with this email is already registered"}
        return Response(message,status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def google_login(request):
    print("Request Data:", request.data)  # Log the incoming request data
    if 'tokenId' not in request.data:
        return Response({'error': 'No token provided'}, status=status.HTTP_400_BAD_REQUEST)

    token_id = request.data['tokenId']
    print("Token ID Received:", token_id)  # Log the token ID

    # Verify the token with Google's API
    try:
        print("Verifying token...")
        request_adapter = google_requests.Request()
        id_info = id_token.verify_oauth2_token(token_id, request_adapter, audience='845512665517-sqrndab2vlttb0o4lba1nivu6civ38h4.apps.googleusercontent.com')
        print("Token verified successfully!")

        uid = id_info['sub']  # Unique user ID from Google
        print("UID:", uid)

        # Try to get the user based on the Google UID
        try:
            print("Getting social account...")
            social_account = SocialAccount.objects.get(provider='google', uid=uid)
            user = social_account.user
            print("Social account found!")
        except SocialAccount.DoesNotExist:
            print("Social account not found, creating new user...")
            username = id_info['email'].split('@')[0] + str(uuid.uuid4())[:8]  # Generate a unique username
            user = User.objects.create_user(username, email=id_info['email'])
            social_account = SocialAccount.objects.create(user=user, provider='google', uid=uid)
            print("New user created!")

        serializer = UserSerializerWithToken(user, many=False)
        return Response(serializer.data)

    except ValueError as e:
        print("Invalid token:", e)
        return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        print("Error occurred:", e)
        return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from rest_framework.permissions import AllowAny
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    # Debug information
    print("Request method:", request.method)
    print("Request user:", request.user)
    print("Request auth:", request.auth)
    print("Request data:", request.data)
    email = request.data.get('email')
    print(email)
    if not email:
        print("hi")
        return Response({'error': 'Email is required'}, status=400)

    user = User.objects.filter(email=email).first()
    print(user)

    if user:
        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create password reset link
        reset_link = f"http://localhost:3000/#/passwordreset/{uid}/{token}"
        
        # Send email
        subject = "Password Reset Request"
        message = f"Click on this link to reset your password: {reset_link}"
        print("Before sending email")  # Add this before the send_mail call

        try:
            send_mail(subject, message, 'vendorverse833@gmail.com', [email])
            print("Email sent successfully")
        except Exception as e:
            print(f"Error sending email: {e}")

        return Response({'message': 'Password reset email sent'}, status=200)
    else:
        # Don't reveal that the user doesn't exist
        return Response({'message': 'If an account with this email exists, a password reset link has been sent.'}, status=200)

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_bytes(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        new_password = request.data.get('new_password')
        if new_password:
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password has been reset successfully.'}, status=200)
        else:
            return Response({'error': 'New password is required.'}, status=400)
    else:
        return Response({'error': 'Invalid reset link or token.'}, status=400)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserProfile(request):
    user =request.user 
    serializer = UserSerializer(user,many = False)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateUserProfile(request):
    user =request.user 
    serializer = UserSerializerWithToken(user,many = False)
    data = request.data
    user.first_name = data['name']
    user.username = data['email']
    user.email = data['email']
    if data['password'] !="":
        user.password= make_password(data['password'])
    user.save()
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def getUsers(request):
    users = User.objects.all()
    serializer = UserSerializer(users,many = True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAdminUser])
def getUserById(request,pk):
    users = User.objects.get(id=pk)
    serializer = UserSerializer(users,many = False)
    return Response(serializer.data)



@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateUser(request,pk):
    user =User.objects.get(id=pk)
   
    data = request.data
    user.first_name = data['name']
    user.username = data['email']
    user.email = data['email']
    user.is_staff = data['isAdmin']
    
    user.save()
    serializer = UserSerializer(user,many = False)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def deleteUser(request,pk):
    userForDeletion = User.objects.get(id=pk)
    userForDeletion.delete()
    return Response("User was deleted")



