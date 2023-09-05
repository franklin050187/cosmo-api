from shipcomcot import com
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

@app.get('/analyze')
async def analyze(request: Request):
    query = request.query_params
    data = query["url"]
    # data = unquote_plus(data)
    print(data)
    if not data:
        return "No data"
    else:
        result = com(data)
        result = json.loads(result)
        return result

app.add_middleware(SessionMiddleware, secret_key="121298102981092")
app.add_middleware(GZipMiddleware, minimum_size=1000)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8001)

    