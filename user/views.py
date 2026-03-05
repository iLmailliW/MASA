from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from .models import Company
import datetime


def index(request):
    if request.method == 'POST':

        new_company = Company.objects.create(
            name=request.POST.get("name"),
            industry=request.POST.get("industry"),
            country=request.POST.get("country"),
            city=request.POST.get("city"),
            year=request.POST.get("year"),
            proj_ebitda=request.POST.get("proj_EBITDA"),
            company_ebitda=request.POST.get("company_EBITDA"),
            value=request.POST.get("value"),
            risk=request.POST.get("risk"),
            date=datetime.date.today()
        )
        # save data here if needed
        return HttpResponseRedirect(reverse('user:response', args=(new_company.name,)))

    return render(request, "user/index.html")

def response(request, name):
    company = get_object_or_404(Company, name=name)
    country = company.country
    company_data = {
        "name": company.name,
        "industry": company.industry,
        "country": company.country,
        "city": company.city,
        "year": company.year,
        "proj_EBITDA": company.proj_ebitda,
        "company_EBITDA": company.company_ebitda,
        "value": company.value,
        "risk": company.risk,
        "date": company.date
    }
    company.delete()
    context = {}
    return render(request, "user/response.html", context)
