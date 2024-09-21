from django.urls import path
from base.views import user_views as views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('passwordreset/', views.password_reset_request),
    # path('passwordreset/<uidb64>/<token>/', views.password_reset_confirm),
    path('register/',views.registerUser,name='register'),
    path('google-login/',views.google_login,name="google-login"),
    path('',views.getUsers,name="users"),
    path('profile/',views.getUserProfile,name="user_profile"),
    path('profile/update/',views.updateUserProfile,name="user_profile_update"),
    path('login/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('<str:pk>/',views.getUserById,name="get_user"),
    path('update/<str:pk>/',views.updateUser,name="updateUser"),
    path('delete/<str:pk>/',views.deleteUser,name="deleteUser"),
]
