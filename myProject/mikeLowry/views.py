from django.http import FileResponse
from django.shortcuts import render

def landing(request):
    return render(request=request, template_name="index.html")

def render_paper(request):
    return render(request=request, template_name="graph.html")

def show_image(request):
    return render(request=request, template_name="graph.html")
