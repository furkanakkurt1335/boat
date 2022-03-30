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
    path('view_treebanks/', views.view_treebanks, name='view_treebanks'),
    path('view_treebank/<slug:treebank>/<int:page>', views.view_treebank, name='view_treebank'),
    path('annotate/<slug:treebank>/<int:order>', views.annotate, name='annotate'),
    path('search/', views.search, name='search'),
    path('help/', views.help, name='help'),
    path('accounts/preferences/', views.preferences, name='preferences'),
    path('error/', views.error, name='error'),
    path('spacy/', views.spacy, name='spacy'),
    path('ud_graph/', views.ud_graph, name='ud_graph'),
    path('download_conllu/', views.download_conllu, name='download_conllu'),
]
