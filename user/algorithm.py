
def calc_risk_appetite(company_value: float, industry_max_value: float, project_ebitda: float,
                       company_ebitda: float) -> float:
    """Return the Risk Appetite of a company based on its entreprise value relative to the industry leader and the
    portion of total EBITDA represented by the project.

    Preconditions:
        - 0 <= company_value <= industry_max_value
        - 0 <= project_ebitda <= company_ebitda
        - industry_max_value > 0
        - company_ebitda > 0

    >>> calc_risk_appetite(500000, 1000000, 20000, 100000) # (0.5 + 0.2) / 2
    0.35
    """
    company_value = min(company_value, industry_max_value)
    project_ebitda = min(project_ebitda, company_ebitda)
    size_ratio = company_value / industry_max_value
    revenue_stake = project_ebitda / company_ebitda
    return round((size_ratio + revenue_stake) / 2, 3)


def calc_logistics_iot(port_congestion: float, vessel_tracking: float, weather: float) -> float:
    """Calculate the weighted risk score for Logistics and IoT data.
    Weights: Port Congestion Index (40%), Real-Time AIS Vessel Tracking (40%), Weather / Climate Events (20%).

    Preconditions:
        - 0.0 <= port_congestion, vessel_tracking, weather <= 1.0

    >>> calc_logistics_iot(0.8, 0.5, 0.2) # (0.32 + 0.2 + 0.04)
    0.56
    """
    return (0.4 * port_congestion) + (0.4 * vessel_tracking) + (0.2 * weather)


def calc_supplier_health(credit_risk_scores: float, payment_performance: float, ownership: float) -> float:
    """Calculate the weighted risk score for Supplier Health.
    Weights: Credit / Risk Scores (50%), Payment Performance (30%), Ownership Activity (20%).

    Preconditions:
        - 0.0 <= credit_risk_scores, payment_performance, ownership <= 1.0

    >>> calc_supplier_health(0.9, 0.1, 0.5) # (0.45 + 0.03 + 0.1)
    0.58
    """
    return (0.5 * credit_risk_scores) + (0.3 * payment_performance) + (0.2 * ownership)


def calc_news_geopolitics(trade_policy: float, geopolitical_conflict: float, commodity_volatility: float) -> float:
    """Calculate the weighted risk score for News and Geopolitical Feeds.
    Weights: Trade Policy & Tariffs (50%), Geopolitical Conflict (30%), Commodity Price Volaitility (20%).

    Preconditions:
        - 0.0 <= trade_policy, geopolitical_conflict, commodity_volatility <= 1.0

    >>> calc_news_geopolitics(0.7, 0.8, 0.4) # (0.35 + 0.24 + 0.08)
    0.67
    """
    return (0.5 * trade_policy) + (0.3 * geopolitical_conflict) + (0.2 * commodity_volatility)


def calc_inventory(on_hand: float, safety_stock: float, reorder_points: float) -> float:
    """Calculate the weighted risk score for Inventory.
    Weights: On-Hand Inventory (50%), Safety Stock Levels (30%), Reorder Points (20%).

    Preconditions:
        - 0.0 <= on_hand, safety, reorder <= 1.0

    >>> calc_inventory(0.2, 0.4, 0.9) # (0.1 + 0.12 + 0.18)
    0.4
    """
    return (0.5 * on_hand) + (0.3 * safety_stock) + (0.2 * reorder_points)


def calc_production(order_backlog: float, production_schedule: float) -> float:
    """Calculate the weighted risk score for Production & Demand.
    Weights: Order Backlog (60%), Production Schedule (40%).

    Preconditions:
        - 0.0 <= backlog, schedule <= 1.0

    >>> calc_production(0.8, 0.3) # (0.48 + 0.12)
    0.6
    """
    return (0.6 * order_backlog) + (0.4 * production_schedule)


def calc_procurement(supplier_concentration: float, lead_time_sensitivity: float) -> float:
    """Calculate the weighted risk score for Supplier & Procurement risk.
    Weights: Supplier Concentration (60%), Lead-time Sensitivity (40%).

    Preconditions:
        - 0.0 <= concentration, lead_time <= 1.0

    >>> calc_procurement(0.9, 0.5) # (0.54 + 0.2)
    0.74
    """
    return (0.6 * supplier_concentration) + (0.4 * lead_time_sensitivity)


def calc_external(logistics_iot: float, supplier_health: float, news_geopolitics: float) -> float:
    """Calculate the total External Risk score by weighting three global signal categories.
    Weights: Logistics/IoT (50%), Supplier Health (30%), News/Geopolitics (20%).

    Preconditions:
        - 0.0 <= logistics_iot, supplier_health, news_geopolitics <= 1.0

    >>> calc_external(0.8, 0.4, 0.5) # (0.4 + 0.12 + 0.1)
    0.62
    """
    return (0.5 * logistics_iot) + (0.3 * supplier_health) + (0.2 * news_geopolitics)


def calc_internal(inventory: float, production: float, procurement: float) -> float:
    """Calculate the total Internal Risk score by weighting operational data categories.
    Weights: Inventory (30%), Production (45%), Procurement (25%).

    Preconditions:
        - 0.0 <= inventory, production, procurement <= 1.0

    >>> calc_internal(0.2, 0.6, 0.8) # (0.06 + 0.27 + 0.2)
    0.53
    """
    return (0.3 * inventory) + (0.45 * production) + (0.25 * procurement)


def calc_risk_score(external: float, internal: float) -> float:
    """Calculate the final aggregate Risk Score by balancing external and internal inputs.
    Weights: External Data (50%) and Internal Data (50%).

    Preconditions:
        - 0.0 <= external, internal <= 1.0

    >>> calc_risk_score(0.62, 0.53) # (0.31 + 0.265)
    0.575
    """
    return round((0.5 * external) + (0.5 * internal), 3)


def risk_score_assessment(risk_score: float, risk_appetite: float) -> str:
    """ Return the interpretation of the risk score dependent on the company's risk appetite. The interpretation is
    out of these three options: ["High Risk", "Moderate - High Risk", "Moderate Risk", "Moderate - Low Risk", "Low
    Risk", "Minimal Risk"]

    Preconditions:
        - 0 <= score, appetite <= 1

    >>> risk_score_assessment(0.8, 0.5)
    "High Risk"
    >>> risk_score_assessment(0.45, 0.5)
    "High Risk"
    >>> risk_score_assessment(0.3, 0.5)
    "Moderate - High Risk"
    >>> risk_score_assessment(0.1, 0.5)
    "Moderate Risk"
    >>> risk_score_assessment(0.2, 0.8)
    "Moderate - Low Risk"
    >>> risk_score_assessment(0.1, 0.9)
    "Low Risk"
    >>> risk_score_assessment(0.05, 1.0)
    "Minimal Risk"
    """
    if risk_score >= risk_appetite:
        return "High Risk"
    else:
        diff = risk_appetite - risk_score
        if diff < 0.1:
            return "High Risk"
        elif diff < 0.3:
            return "Moderate - High Risk"
        elif diff < 0.5:
            return "Moderate Risk"
        elif diff < 0.75:
            return "Moderate - Low Risk"
        elif diff < 0.9:
            return "Low Risk"
        else:
            return "Minimal Risk"


def generate_all_sub_sub_risk_scores(logistics_iot: float, supplier_health: float, news_geopolitics: float,
                                     inventory: float, production: float, procurement: float) -> dict[str, float]:
    """ Return a dictionary mapping each supply chain criteria to its calculated risk severity score.

    Preconditions:
        - 0.0 <= logistics_iot, supplier_health, news_geopolitics, inventory, production, procurement <= 1.0
    """
    return {"Logistics/IOT": logistics_iot,
            "Supplier Health": supplier_health,
            "News/Geopolitics": news_geopolitics,
            "Inventory": inventory,
            "Production": production,
            "Procurement": procurement}


def identify_severe_risks(scores: dict[str, float]) -> list[str]:
    """Identify and return the keys of severe risks from the scores dictionary. A risk is severe if its score is > 0.5.
    If no risks meet this threshold, return the 3 highest risk categories.

    Preconditions:
        - scores is a dictionary mapping strings to floats between 0.0 and 1.0, with the same format as the output of
          generate_all_sub_sub_risk_scores().
    """
    severe_risks = [key for key, value in scores.items() if value > 0.5]
    if not severe_risks:
        sorted_scores = sorted(scores.items(), key=lambda category: category[1], reverse=True)
        severe_risk_category_and_scores = sorted_scores[:3]
        severe_risks = [category[0] for category in severe_risk_category_and_scores]
    return severe_risks
