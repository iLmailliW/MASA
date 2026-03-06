from dotenv import load_dotenv
from google import genai
from dotenv import load_dotenv
import os


load_dotenv()

# You can pass a key here manually with api_key="", but it will look for GEMINI_API_KEY in .env by default
client = genai.Client()

def process_text_file(file_path, user_query):
    # Upload the file before prompting
    my_file = client.files.upload(file=file_path)

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=[my_file, user_query]
    )

    return response.text

# Test code
if __name__ == "__main__":
    path_to_txt = "gemini_test.txt"
    prompt = "Please extract the key findings from this file."

    try:
        answer = process_text_file(path_to_txt, prompt)
        print(answer)
    except Exception as e:
        print(f"Error: {e}")
