from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    context = {}
    return render(request, "home/index.html", context)

def esg_considerations(request):
    # Any data you want to pass to the template
    context = {}
    return render(request, 'home/esg_considerations.html', context)

def corporate_vision(request):
    # Any data you want to pass to the template
    context = {}
    return render(request, 'home/corporate_vision.html', context)
