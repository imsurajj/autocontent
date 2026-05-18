import urllib.request
import json
import uuid

APPWRITE_ENDPOINT = "https://sgp.cloud.appwrite.io/v1"
APPWRITE_PROJECT_ID = "6a09e8a5002e960936ec"
APPWRITE_FUNCTION_ID = "verify-license"

def call_appwrite_function(action, key, hwid):
    payload = json.dumps({"action": action, "key": key, "hwid": hwid})
    req_body = json.dumps({"async": False, "body": payload}).encode('utf-8')
    
    url = f"{APPWRITE_ENDPOINT}/functions/{APPWRITE_FUNCTION_ID}/executions"
    req = urllib.request.Request(
        url, 
        data=req_body, 
        headers={
            "Content-Type": "application/json", 
            "X-Appwrite-Project": APPWRITE_PROJECT_ID,
            "User-Agent": "AutoContent-Tester/1.0"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            res = json.loads(r.read().decode('utf-8'))
            print("Serverless function execution metadata:", json.dumps(res, indent=2))
            print("Status code:", res.get("responseStatusCode"))
            print("Body:", res.get("responseBody"))
    except Exception as e:
        print("HTTP Error:", e)

# Test deactivation
hwid = str(uuid.getnode())
print(f"Testing deactivation with key='suraj' and hwid='{hwid}'")
call_appwrite_function("deactivate", "suraj", hwid)
