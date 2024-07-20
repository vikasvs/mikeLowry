from django.urls import path
from .views import get_stock_data

urlpatterns = [
    path('stock/<str:query_date>/', get_stock_data, name='get_stock_data'),
]
