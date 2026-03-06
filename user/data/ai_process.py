from google import genai
from dotenv import load_dotenv

load_dotenv()

# You can pass a key here manually with api_key="", but it will look for GEMINI_API_KEY in .env by default
client = genai.Client()

def process_text_file(file_path, user_query):
    # Upload the file before prompting
    my_file = client.files.upload(file=file_path, config={"mime_type": "text/csv", "display_name": "data"})

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=[my_file, user_query],

    )

    return response.text

def process_string(prompt, user_query):
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents = prompt + " " + user_query
    )

    return response.text



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
