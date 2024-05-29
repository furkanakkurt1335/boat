"""django_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from search import views

router = routers.DefaultRouter()
router.register('users', views.UserViewSet)
router.register('groups', views.GroupViewSet)
router.register('treebanks', views.TreebankViewSet)
router.register('sentences', views.SentenceViewSet)
router.register('annotations', views.AnnotationViewSet)
router.register('wordlines', views.WordLineViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('ui.urls')),
    # path('', include('search.urls')),
    path('query/', views.query, name='query'),
    path('api/my_annotations/', views.my_annotations, name='my_annos'),
    path('api/get_treebank/', views.get_treebank, name='get_treebank'),
    path('api/get_annotations/', views.get_annotations, name='get_annotations'),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
