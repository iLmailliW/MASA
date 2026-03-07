from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from .models import Company, MarketCaps
from datetime import datetime
from .algorithm import *
from .data.ai_process import *


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
            time=datetime.now()
        )
        # save data here if needed
        return HttpResponseRedirect(reverse('user:response', args=(new_company.id,)))

    return render(request, "user/index.html")


# This method renders the results page. It has to call any function necessary to get the result
def response(request, company_id):
    company = get_object_or_404(Company, pk=company_id)

    try:
        marketcaps = MarketCaps.objects.get(date=date.today())
    except MarketCaps.DoesNotExist:
        marketcaps = MarketCaps(data=search_sp500_marketcaps(), date=date.today())
        marketcaps.save()
    industry_max_value = get_largest_enterprise_value(company.industry, MarketCaps.objects.get(date=date.today()).data)
    risk_appetite = calc_risk_appetite(company_value=company.value,
                                                 industry_max_value=industry_max_value,
                                                 project_ebitda=company.proj_ebitda,
                                                 company_ebitda=company.company_ebitda)
    port_congestion = get_port_congestion_index()["index"]
    logistics_iot = port_congestion
    credit_risk_scores = get_credit_risk_score()["index"]
    payment_performance_ownership_activity = get_payment_performance_ownership_activity()
    payment_performance = payment_performance_ownership_activity["index"]
    ownership = payment_performance_ownership_activity["index2"]
    supplier_health = calc_supplier_health(credit_risk_scores=credit_risk_scores,
                                                     payment_performance=payment_performance,
                                                     ownership=ownership)
    trade_policy = get_tarrifs_news()["index"]
    geopolitical_conflict = get_geopolitical_data()["index"]
    news_geopolitics = calc_news_geopolitics(trade_policy=trade_policy,
                                                       geopolitical_conflict=geopolitical_conflict)
    risk_score = calc_risk_score(logistics_iot=logistics_iot,
                                           supplier_health=supplier_health,
                                           news_geopolitics=news_geopolitics)
    assessment = risk_score_assessment(risk_score, risk_appetite)
    sub_sub_risk_scores = generate_all_sub_sub_risk_scores(port_congestion=port_congestion,
                                                           credit_risk_scores=credit_risk_scores,
                                                           payment_performance=payment_performance,
                                                           ownership=ownership,
                                                           trade_policy=trade_policy,
                                                           geopolitical_conflict=geopolitical_conflict)
    severe_risks = identify_severe_risks(sub_sub_risk_scores)
    analysis = []
    if "Port Congestion Index" in severe_risks:
        analysis.append(mitigation_port_congestion())
    if "Credit / Risk Scores" in severe_risks:
        analysis.append(mitigation_credit_risk())
    if "Payment Performance" in severe_risks:
        analysis.append(mitigation_payment_performance())
    if "Ownership Activity" in severe_risks:
        analysis.append(mitigation_ownership_activity())
    if "Trade Policy & Tariffs" in severe_risks:
        analysis.append(mitigation_trade_policy())
    if "Geopolitical Conflict" in severe_risks:
        analysis.append(mitigation_geopolitical_conflict())




    result_dict = {"Company Name": company.name,
                   "Company Industry": company.industry,
                   "Risk Appetite": risk_appetite,
                   "Risk Score": risk_score,
                   "Assessment": assessment, # low-high risk
                   "Severe Risk Categories": severe_risks, # template name
                   "Analysis": analysis # mitigation strategies
                   }
    return render(request, "user/response.html", result_dict)
