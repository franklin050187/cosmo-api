from shipcomcot import analyze_ship
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn
import json

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post('/analyze')
async def analyze(request: Request):
    # Retrieve the raw request body as bytes
    request_body = await request.body()
    
    # Parse the request body as JSON
    json_data = json.loads(request_body.decode('utf-8'))
    data = json.loads(json_data)
    result = analyze_ship(data)
    return result

app.add_middleware(SessionMiddleware, secret_key="121298102981092")
app.add_middleware(GZipMiddleware, minimum_size=1000)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8001)

    