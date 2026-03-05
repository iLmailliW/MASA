from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return HttpResponse("We are Masa! bum badum ba dum dum dum")
