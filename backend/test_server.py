
import requests
import json

def test_health_endpoint():
    response = requests.get("http://localhost:8000/health")
    print(f"Health check: {response.status_code} - {response.json()}")

def test_generate_endpoint():
    # This is a basic test - you'd need actual files and API keys
    print("Generate endpoint requires file upload and API key - test manually")

if __name__ == "__main__":
    test_health_endpoint()
    test_generate_endpoint()
