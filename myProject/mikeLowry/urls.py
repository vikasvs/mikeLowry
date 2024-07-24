from django.urls import path
from . import views

urlpatterns = [
    path('index/', views.landing, name='index'),
    path('show_image/', views.show_image, name='show_image'),
    # Add other paths here
]
