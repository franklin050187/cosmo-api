from fastapi import FastAPI, Request
from shipcomcot import analyze_ship
import json
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
from fastapi.middleware.gzip import GZipMiddleware
import os

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
    
# session settings
app.add_middleware(SessionMiddleware, secret_key=os.getenv('secret_session'))
app.add_middleware(GZipMiddleware, minimum_size=1000)

# start server
if __name__ == '__main__':
    uvicorn.run(app)
