from base.views import user_views as views
from django.urls import path

urlpatterns = [
    path('passwordreset/<uidb64>/<token>/', views.password_reset_confirm),
    
]

