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
            time=datetime.datetime.now()
        )
        # save data here if needed
        return HttpResponseRedirect(reverse('user:response', args=(new_company.id,)))

    return render(request, "user/index.html")


#This method renders the results page. It has to call any function necessary to get the result
def response(request, company_id):
    company = get_object_or_404(Company, pk=company_id)
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
        "time": company.time
    }
    assessment = risk_score_assessment(score=0.5, appetite=company_data["risk"])
    context = {"risk_assessment": assessment}
    #TODO: call all functions to get and process data
    return render(request, "user/response.html", context)
