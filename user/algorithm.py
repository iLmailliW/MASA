
def calc_risk_appetite(company_value: float,
                       industry_max_value: float,
                       project_ebitda: float,
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


def calc_supplier_health(credit_risk_scores: float,
                         payment_performance: float,
                         ownership: float) -> float:
    """Calculate the weighted risk score for Supplier Health.
    Weights: Credit / Risk Scores (50%), Payment Performance (30%), Ownership Activity (20%).

    Preconditions:
        - 0.0 <= credit_risk_scores, payment_performance, ownership <= 1.0

    >>> calc_supplier_health(0.9, 0.1, 0.5) # (0.45 + 0.03 + 0.1)
    0.58
    """
    return (0.5 * credit_risk_scores) + (0.3 * payment_performance) + (0.2 * ownership)


def calc_news_geopolitics(trade_policy: float,
                          geopolitical_conflict: float) -> float:
    """Calculate the weighted risk score for News and Geopolitical Feeds.
    Weights: Trade Policy & Tariffs (60%), Geopolitical Conflict (40%).

    Preconditions:
        - 0.0 <= trade_policy, geopolitical_conflict <= 1.0
    """
    return (0.6 * trade_policy) + (0.4 * geopolitical_conflict)


def calc_risk_score(logistics_iot: float,
                    supplier_health: float,
                    news_geopolitics: float) -> float:
    """Calculate the final aggregate Risk Score by weighting three global signal categories.
    Weights: Logistics/IoT (50%), Supplier Health (30%), News/Geopolitics (20%).

    Preconditions:
        - 0.0 <= logistics_iot, supplier_health, news_geopolitics <= 1.0

    >>> calc_risk_score(0.8, 0.4, 0.5) # (0.4 + 0.12 + 0.1)
    0.62
    """
    return (0.5 * logistics_iot) + (0.3 * supplier_health) + (0.2 * news_geopolitics)


def risk_score_assessment(risk_score: float,
                          risk_appetite: float) -> str:
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


def generate_all_sub_sub_risk_scores(port_congestion: float,
                                     credit_risk_scores: float,
                                     payment_performance: float,
                                     ownership: float,
                                     trade_policy: float,
                                     geopolitical_conflict: float) -> dict[str, float]:
    """ Return a dictionary mapping each supply chain criteria to its calculated risk severity score.

    Preconditions:
        - 0.0 <= logistics_iot, supplier_health, news_geopolitics, inventory, production, procurement <= 1.0
    """
    return {"Port Congestion Index": port_congestion,
            "Credit / Risk Scores": credit_risk_scores,
            "Payment Performance": payment_performance,
            "Ownership Activity": ownership,
            "Trade Policy & Tariffs": trade_policy,
            "Geopolitical Conflict": geopolitical_conflict}


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
