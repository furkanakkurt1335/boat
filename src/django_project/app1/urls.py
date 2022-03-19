from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('accounts/login/', views.login, name='login'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/profile/', views.profile, name='profile'),
    path('accounts/logout/', views.logout, name='logout'),
    path('upload_file/', views.upload_file, name='upload_file'),
    path('test/', views.test, name='test'),
    path('create_treebank/', views.create_treebank, name='create_treebank'),
    path('view_treebank/<slug:treebank>', views.view_treebank, name='view_treebank'),
]
