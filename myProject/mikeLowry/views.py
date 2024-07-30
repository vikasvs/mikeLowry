from django.shortcuts import render
from django.http import JsonResponse
import os
import json
from django.conf import settings
from authlib.integrations.django_client import OAuth
from django.urls import reverse
from django.shortcuts import redirect, render, redirect
from urllib.parse import quote_plus, urlencode

oauth = OAuth()

oauth.register(
    "auth0",
    client_id=settings.AUTH0_CLIENT_ID,
    client_secret=settings.AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
)

def landing(request):
    return render(request, 'index.html', 
                  context={
                      "session": request.session.get("user")
                      })

def callback(request):
    token = oauth.auth0.authorize_access_token(request)
    request.session["user"] = token
    return redirect(request.build_absolute_uri(reverse("landing")))

def login(request):
    return oauth.auth0.authorize_redirect(
        request, request.build_absolute_uri(reverse("callback"))
    )

def logout(request):
    request.session.clear()

    return redirect(
        f"https://{settings.AUTH0_DOMAIN}/v2/logout?"
        + urlencode(
            {
                "returnTo": request.build_absolute_uri(reverse("index")),
                "client_id": settings.AUTH0_CLIENT_ID,
            },
            quote_via=quote_plus,
        ),
    )


# def render_paper(request):
#     return render(request, 'graph.html')

# def show_image(request):
#     return render(request, 'graph.html')

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
