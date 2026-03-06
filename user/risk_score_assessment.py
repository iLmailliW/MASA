def risk_score_assessment(score: float, appetite: float) -> str:
    """ Return the interpretation of the risk score dependent on the company's risk appetite. The interpretation is
    out of these three options: ["High Risk", "Moderate - High Risk", "Moderate Risk", "Moderate - Low Risk", "Low
    Risk", "Minimal Risk"]

    Preconditions:
        - 0 <= score <= 1
        - 0 <= appetite <= 1

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
    if score >= appetite:
        return "High Risk"
    else:
        diff = appetite - score
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

