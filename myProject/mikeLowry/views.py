from django.shortcuts import render
from django.http import JsonResponse
import os
import json
from django.conf import settings

def landing(request):
    return render(request, 'index.html')

def render_paper(request):
    return render(request, 'graph.html')

def show_image(request):
    return render(request, 'graph.html')

def get_plotly_data(request, year, timeframe):
    # Update this path to where your static files are located
    json_file_path = os.path.join(settings.BASE_DIR, 'static', f'{year}_{timeframe}_plotly.json')
    
    # Print the file path to debug
    print(f"Checking file path: {json_file_path}")
    
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)
        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'File not found'}, status=404)
