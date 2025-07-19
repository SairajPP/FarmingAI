from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-crop/', views.add_crop, name='add_crop'),
    path('chatbot-reply/', views.chatbot_reply, name='chatbot_reply'),
    path('upload_crop_image/', views.upload_crop_image, name='upload_crop_image'),
    path('update-profile/', views.update_profile, name='update_profile'),

]
