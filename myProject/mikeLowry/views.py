from django.http import JsonResponse
from .models import Stock
from datetime import date

def get_stock_data(request, query_date):
    try:
        stock = Stock.objects.get(date=query_date)
        data = {
            'date': stock.date,
            'closing_price': stock.closing_price,
            'signal': stock.signal
        }
        return JsonResponse(data)
    except Stock.DoesNotExist:
        return JsonResponse({'error': 'Data not found'}, status=404)
