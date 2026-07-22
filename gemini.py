import requests

API_KEY = "20bf8daf-a5a5-423d-b442-01717a9baa98"

url = "https://labs.pluralsight.com/labs-ai-proxy/"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

response = requests.get(url, headers=headers)

print("Status Code:", response.status_code)
print("Response:")
print(response.text)