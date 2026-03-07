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
            time=datetime.now(),
            cik=request.POST.get("cik"),
            symbol=request.POST.get("symbol")
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
    port_congestion = get_port_congestion_index()
    logistics_iot = port_congestion
    credit_risk_scores = get_credit_risk_score(company.symbol)
    payment_performance_ownership_activity = get_payment_performance_ownership_activity(company.cik, company.symbol)
    payment_performance = payment_performance_ownership_activity["index"]
    ownership = payment_performance_ownership_activity["index2"]
    supplier_health = calc_supplier_health(credit_risk_scores=credit_risk_scores["index"],
                                                     payment_performance=payment_performance,
                                                     ownership=ownership)
    trade_policy = get_tarrifs_news()
    geopolitical_conflict = get_geopolitical_data()
    news_geopolitics = calc_news_geopolitics(trade_policy=trade_policy["index"],
                                                       geopolitical_conflict=geopolitical_conflict["index"])
    risk_score = calc_risk_score(logistics_iot=logistics_iot["index"],
                                           supplier_health=supplier_health,
                                           news_geopolitics=news_geopolitics)
    assessment = risk_score_assessment(risk_score, risk_appetite)
    sub_sub_risk_scores = generate_all_sub_sub_risk_scores(port_congestion=port_congestion["index"],
                                                           credit_risk_scores=credit_risk_scores["index"],
                                                           payment_performance=payment_performance,
                                                           ownership=ownership,
                                                           trade_policy=trade_policy["index"],
                                                           geopolitical_conflict=geopolitical_conflict["index"])
    severe_risks = identify_severe_risks(sub_sub_risk_scores)
    analysis = []
    if "Port Congestion Index" in severe_risks:
        analysis.append(mitigation_port_congestion(sub_sub_risk_scores["Port Congestion Index"], str(port_congestion["data"])))
    if "Credit / Risk Scores" in severe_risks:
        analysis.append(mitigation_credit_risk(sub_sub_risk_scores["Port Congestion Index"], str(credit_risk_scores["data"])))
    if "Payment Performance" in severe_risks:
        analysis.append(mitigation_payment_performance(sub_sub_risk_scores["Port Congestion Index"], str(payment_performance_ownership_activity["data"])))
    if "Ownership Activity" in severe_risks:
        analysis.append(mitigation_ownership_activity(sub_sub_risk_scores["Port Congestion Index"], str(payment_performance_ownership_activity["data"])))
    if "Trade Policy & Tariffs" in severe_risks:
        analysis.append(mitigation_trade_policy(sub_sub_risk_scores["Port Congestion Index"], str(trade_policy["data"])))
    if "Geopolitical Conflict" in severe_risks:
        analysis.append(mitigation_geopolitical_conflict(sub_sub_risk_scores["Port Congestion Index"], str(geopolitical_conflict["data"])))

    superprompt = f'Do not include any *, #, or newlines. ROLE\nYou are a Senior Supply Chain Risk Consultant and Legal Drafting Specialist. Below, you will receive a data containing company profile information and risk analysis.\n\n### INSTRUCTIONS\n1. Parse the result_dict to identify Company Name, Company Industry, and Risk_Appetite. Use these to set the professional tone.\n2. Cross-reference the Severe_Risk_Categories list against the Analysis mitigation strategies.\n3. ONLY generate formal documents for the specific categories named in Severe_Risk_Categories. If a category is not in that list, do not generate a document for it.\n\n### MITIGATION FRAMEWORK\n- Port Congestion Index -> Draft "Logistics Redirection Memo" and "Urgent Air Freight SLA".\n- Credit / Risk Scores -> Draft "Notice of Amendment to Payment Terms".\n- Payment Performance -> Draft "Supplier Audit Notification" and "Supply Chain Finance (SCF) Program Enrollment Offer".\n- Ownership Activity -> Draft "Market Competition Comp. '



    result_dict = {"Company_Name": company.name,
                   "Company_Industry": company.industry,
                   "Risk_Appetite": risk_appetite,
                   "Risk_Score": risk_score,
                   "Assessment": assessment, # low-high risk
                   "Severe_Risk_Categories": severe_risks, # template name
                   "Analysis": analysis # mitigation strategies

                   }

    s = process_string(superprompt, str(result_dict))

    result_dict["Action_Plan"] = s

    print(result_dict)

    return render(request, "user/response.html", result_dict)
