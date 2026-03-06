from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from .models import Company
import datetime
import algorithm


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
            time=datetime.datetime.now(),
            on_hand=request.POST.get("on_hand"),
            safety_stock=request.POST.get("safety_stock"),
            reoder_points=request.POST.get("reoder_points"),  # Matches your model typo
            order_backlog=request.POST.get("order_backlog"),
            production_schedule=request.POST.get("production_schedule"),
            supplier_concentration=request.POST.get("supplier_concentration"),
            lead_time_sensitivity=request.POST.get("lead_time_sensitivity")
        )
        # save data here if needed
        return HttpResponseRedirect(reverse('user:response', args=(new_company.id,)))

    return render(request, "user/index.html")


#This method renders the results page. It has to call any function necessary to get the result
def response(request, company_id):
    company = get_object_or_404(Company, pk=company_id)
    industry_max_value = 0.0  #TODO: dependent on William Li (WL)
    risk_appetite = algorithm.calc_risk_appetite(company_value=company.value,
                                                 industry_max_value=industry_max_value,
                                                 project_ebitda=company.proj_ebitda,
                                                 company_ebitda=company.company_ebitda)
    port_congestion = 0.0  # TODO: WL
    vessel_tracking = 0.0  # TODO: WL
    weather = 0.0  # TODO: WL
    logistics_iot = algorithm.calc_logistics_iot(port_congestion=port_congestion,
                                                 vessel_tracking=vessel_tracking,
                                                 weather=weather)
    credit_risk_scores = 0.0  # TODO: WL
    payment_performance = 0.0  # TODO: WL
    ownership = 0.0  # TODO: WL
    supplier_health = algorithm.calc_supplier_health(credit_risk_scores=credit_risk_scores,
                                                     payment_performance=payment_performance,
                                                     ownership=ownership)
    trade_policy = 0.0  # TODO: WL
    geopolitical_conflict = 0.0  # TODO: WL
    commodity_volatility = 0.0  # TODO: WL
    news_geopolitics = algorithm.calc_news_geopolitics(trade_policy=trade_policy,
                                                       geopolitical_conflict=geopolitical_conflict,
                                                       commodity_volatility=commodity_volatility)
    on_hand = company.on_hand
    safety_stock = company.safety_stock
    reorder_points = company.reorder_points
    inventory = algorithm.calc_inventory(on_hand=on_hand,
                                         safety_stock=safety_stock,
                                         reorder_points=reorder_points)
    order_backlog = company.order_backlog
    production_schedule = company.production_schedule
    production = algorithm.calc_production(order_backlog=order_backlog,
                                           production_schedule=production_schedule)
    supplier_concentration = company.supplier_concentration
    lead_time_sensitivity = company.lead_time_sensitivity
    procurement = algorithm.calc_procurement(supplier_concentration=supplier_concentration,
                                             lead_time_sensitivity=lead_time_sensitivity)
    external = algorithm.calc_external(logistics_iot=logistics_iot,
                                       supplier_health=supplier_health,
                                       news_geopolitics=news_geopolitics)
    internal = algorithm.calc_internal(inventory=inventory,
                                       production=production,
                                       procurement=procurement)
    risk_score = algorithm.calc_risk_score(external=external,
                                           internal=internal)
    assessment = algorithm.risk_score_assessment(risk_score, risk_appetite)
    sub_sub_risk_scores = algorithm.generate_all_sub_sub_risk_scores(logistics_iot=logistics_iot,
                                                                     supplier_health=supplier_health,
                                                                     news_geopolitics=news_geopolitics,
                                                                     inventory=inventory,
                                                                     production=production,
                                                                     procurement=procurement)
    severe_risks = algorithm.identify_severe_risks(sub_sub_risk_scores)
    analysis = ""
    result_dict = {"Risk Appetite": risk_appetite,
                   "External Score": external,
                   "Internal Score": internal,
                   "Risk Score": risk_score,
                   "Assessment": assessment,
                   "Severe Risk Categories": severe_risks,
                   "Analysis": analysis
                   }
    #TODO: call all functions to get and process data
    return render(request, "user/response.html", result_dict)

