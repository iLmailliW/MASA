import data
from datetime import date
import os
import dotenv

dotenv.load_dotenv()

def test_search_gdelt(keywords=("hurricane", "typhoon", "cyclone"),
                      project_id="masa-489401",
                      match_all=False,
                      days_back=7,
                      limit=100,
                      output_file=""):
    return data.search_gdelt(
        keywords,
        project_id,
        "credentials.json",
        match_all,
        days_back,
        limit,
        output_file,
    )
    # for article in results:
    #     print(f"{article['published_at']}  {article['title']}")
    #     print(f"  {article['url']}\n")


def test_search_portwatch(days_back=30):
    return data.search_portwatch(days_back=days_back)


def test_search_edgar():
    data.search_edgar_financials(
        cik="0001706431",
        company_name="Vir Biotechnology, Inc",
        output_file="vir_financials.csv",  # optional
    )

