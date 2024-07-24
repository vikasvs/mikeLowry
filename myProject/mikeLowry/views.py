from django.http import FileResponse
from django.shortcuts import render

def landing(request):
    return render(request=request, template_name="index.html")

def render_paper(request):
    # return FileResponse(open("./mikeLowry/paper_backend/resources/graph.png", "rb"), filename="graph")
    return render(request=request, template_name="graph.html")

