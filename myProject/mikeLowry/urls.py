from django.urls import path
from .views import landing, render_paper

urlpatterns = [
    path('index/', landing, name="landing_page"),
    path('paper1/', render_paper, name="paper 1")
    # render_graph
]
