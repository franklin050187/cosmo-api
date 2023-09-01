from fastapi import FastAPI, Request
from shipcomcot import analyze_ship
import json

app = FastAPI()

@app.get("/analyze")
async def analyze(request: Request):
    # Get the query parameters from the request URL
    query_params = request.query_params
    # print("query_param_get = ",query_params)
    if not query_params['url']:
            # Create a dictionary with your values
        data = {
        "error": "No URL provided",
        }
        return json.dumps(data)
    else:
        url = query_params['url']
        return analyze_ship(url)