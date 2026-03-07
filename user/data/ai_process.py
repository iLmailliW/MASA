import datetime

from google import genai
from dotenv import load_dotenv
import data
import os

from user.data.data import search_credit_risk, search_edgar_financials, search_portwatch

load_dotenv()

# You can pass a key here manually with api_key="", but it will look for GEMINI_API_KEY in .env by default
client = genai.Client()

def process_text_file(file_path, user_query):
    """ Upload the file before prompting
    """
    my_file = client.files.upload(file=file_path, config={"mime_type": "text/csv", "display_name": "data"})

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=[my_file, user_query]
    )

    return response.text

def process_string(prompt, user_query):
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents = prompt + " " + user_query
    )

    return response.text

def get_port_congestion_index():
    port_data = search_portwatch(start_date=str(datetime.date.today() - datetime.timedelta(days=30)), end_date=str(datetime.date.today()))
    print("Prompting...")
    gemini = process_string("give me general global port congestion trends start your response with a value from 0 to 1 that represents the severity of the risk to any supplier overall to 2 decimal places", str(port_data))
    print(gemini[:100])
    # print(f"index: {float(gemini[:5].strip())}")
    return {"index": float(gemini[:5].strip()), "response": gemini, "data": port_data}


def get_credit_risk_score(symbol: str = "GHM"):
    credit_data = search_credit_risk(symbol)
    print("Prompting...")
    gemini = process_string(f"give me a credit/risk score for the company in the following data start your response with a value from 0 to 1 that represents the severity of the risk to any supplier overall to 2 decimal places", str(credit_data))
    print(gemini[:100])
    return {"index": float(gemini[:5].strip()), "response": gemini, "data": credit_data}

def get_payment_performance_ownership_activity(cik: str = "0000716314", symbol: str = "GHM"):
    edgar_data = search_edgar_financials(cik, symbol)
    print("Prompting...")
    gemini = process_string(f"give me an assessment of payment performance and ownership activity with a value from 0 to 1 where 1 represents most risky and 0 represents least start your response with two values from 0 to 1 that represents the severity of the risk to any supplier overall to 2 decimal places, separated by a comma with no spaces", str(edgar_data))
    print(gemini[:100])
    return {"index": float(gemini[:4]), "index2": float(gemini[5:9]), "response": gemini, "data": edgar_data}

def get_tarrifs_news(keywords: tuple[str]):
    gdelt_data = data.search_gdelt(
        list(keywords),
        "masa-489401",
        "credentials.json",
        False,
        50,
        100,
        "",
    )
    print("Prompting...")
    gemini = process_string(
        f"give me an assessment of how the following tarrifs would affect a mid level manufacturer start your response with a value from 0 to 1 that represents the severity overall to 2 decimal places",
        str(gdelt_data))
    print(gemini[:100])
    return {"index": float(gemini[:4]), "response": gemini, "data": gdelt_data}


def get_geopolitical_data(keywords: tuple[str] = ("war", "shortage", "natural disaster", "strike", "cybersecurity")):
    gdelt_data = data.search_gdelt(
        list(keywords),
        "masa-489401",
        "credentials.json",
        False,
        10,
        250,
        "",
    )
    print("Prompting...")
    gemini = process_string(
        f"give me an assessment of how the following geopolitical events would affect a mid level manufacturer start your response with a value from 0 to 1 that represents the severity overall to 2 decimal places",
        str(gdelt_data))
    print(gemini[:100])
    return {"index": float(gemini[:4]), "response": gemini, "data": gdelt_data}

def get_largest_enterprise_value(industry: str, marketcap_data: dict | None):
    if marketcap_data is None:
        marketcap_data = data.search_sp500_marketcaps()
    print("Prompting...")
    gemini = process_string(
        f"get the marketcap of the largest company in the following industry: technology. respond as a single float in terms of billions of dollars",
        str(marketcap_data))
    return float(gemini)

def mitigation_port_congestion(index: float):
    process_string("", "Divert shipments to secondary, less congested ports such as ______. Consider shifting to air travel for critical, high-priority components with partners such as ______.")

def mitigation_credit_risk(index: float):
    pass

def mitigation_payment_performance(index: float):
    pass

def mitigation_ownership_activity(index: float):
    pass

def mitigation_trade_policy(index: float):
    pass

def mitigation_geopolitical_conflict(index: float):
    pass

# Test code
if __name__ == "__main__":
    # path_to_txt = "apple_financials.csv"
    # prompt = "Rate Payment Performance and Ownership activity from 0.00 to 1.00 with 1 indicating high risk and 0 indicating low risk. Be blunt with the ratings."
    #
    # try:
    #     answer = process_text_file(path_to_txt, prompt)
    #     print(answer)
    # except Exception as e:
    #     print(f"Error: {e}")
    pass
