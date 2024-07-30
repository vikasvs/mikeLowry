from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('index/', views.landing, name='index'),  # Ensures index page can be accessed
    # path('render_paper/', views.render_paper, name='render_paper'),
    # path('show_image/', views.show_image, name='show_image'),
    path('data/<str:year>/<str:timeframe>/', views.get_plotly_data, name='get_plotly_data'),
    path('login/', views.login, name='login'),
    path("logout", views.logout, name="logout"),
    path("callback", views.callback, name="callback"),
]
