from shipcomcot import analyze_ship
from mangum import Mangum
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get('/analyze')
def analyze(request: Request):
    query_params = request.query_params

    print("query_param_get = ",query_params)
    if not query_params['url']:
            # Create a dictionary with your values
        data = {
        "error": "No URL provided",
        }
    else:
        url = query_params['url']
        return analyze_ship(url)

app.add_middleware(SessionMiddleware, secret_key="121298102981092")
app.add_middleware(GZipMiddleware, minimum_size=1000)

handler = Mangum(app, lifespan="off")

    