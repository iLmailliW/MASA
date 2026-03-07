from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from .models import Company
import datetime
from user import algorithm
from user.data import ai_process as ai


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


# This method renders the results page. It has to call any function necessary to get the result
def response(request, company_id):
    company = get_object_or_404(Company, pk=company_id)
    industry_max_value = ai.get_largest_enterprise_value(company.industry)
    risk_appetite = algorithm.calc_risk_appetite(company_value=company.value,
                                                 industry_max_value=industry_max_value,
                                                 project_ebitda=company.proj_ebitda,
                                                 company_ebitda=company.company_ebitda)
    port_congestion = ai.get_port_congestion_index()
    logistics_iot = port_congestion
    credit_risk_scores = ai.get_credit_risk_score()
    payment_performance_ownership_activity = ai.get_payment_performance_ownership_activity()
    payment_performance = payment_performance_ownership_activity["Payment Performance"]
    ownership = payment_performance_ownership_activity["Ownership Activity"]
    supplier_health = algorithm.calc_supplier_health(credit_risk_scores=credit_risk_scores,
                                                     payment_performance=payment_performance,
                                                     ownership=ownership)
    trade_policy = ai.get_tarrifs_news()
    geopolitical_conflict = ai.get_geopolitical_data()
    news_geopolitics = algorithm.calc_news_geopolitics(trade_policy=trade_policy,
                                                       geopolitical_conflict=geopolitical_conflict)
    risk_score = algorithm.calc_risk_score(logistics_iot=logistics_iot,
                                           supplier_health=supplier_health,
                                           news_geopolitics=news_geopolitics)
    assessment = algorithm.risk_score_assessment(risk_score, risk_appetite)
    sub_sub_risk_scores = algorithm.generate_all_sub_sub_risk_scores(logistics_iot=logistics_iot,
                                                                     supplier_health=supplier_health,
                                                                     news_geopolitics=news_geopolitics)
    severe_risks = algorithm.identify_severe_risks(sub_sub_risk_scores)
    analysis = ""
    result_dict = {"Company Name": company.name,
                   "Company Industry": company.industry,
                   "Risk Appetite": risk_appetite,
                   "Risk Score": risk_score,
                   "Assessment": assessment,
                   "Severe Risk Categories": severe_risks,
                   "Analysis": analysis
                   }
    #TODO: call all functions to get and process data
    return render(request, "user/response.html", result_dict)
