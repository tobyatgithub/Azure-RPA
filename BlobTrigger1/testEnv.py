import os
from dotenv import load_dotenv

load_dotenv()

# print(os.environ)
endpoint = os.environ["END_POINT"]
apim_key = os.environ["API_KEY"]
print("endpoint = ", endpoint)
print("api key = ", apim_key)