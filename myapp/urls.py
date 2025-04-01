# myapp/urls.py (例)
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload, name='upload'),
    path('get_prompt/', views.get_prompt, name='get_prompt'),
    path('save_prompt/', views.save_prompt, name='save_prompt'),
]