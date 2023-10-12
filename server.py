# from shipcomcot import com
from center_of_mass import com
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn
import json
import os
from comparetool import compare_ships


app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get('/analyze') # get a url
async def analyze(request: Request):
    query = request.query_params
    # get data from url
    url = query["url"]
    args = {}
    query_keys = ["draw", "flip_vectors", "draw_all_com", "draw_all_cot", "draw_cot", "draw_com", "boost", "analyze"]

    for key in query_keys:
        if key in query:
            args[key] = query[key]

    placeholder = "placeholder" # we do not output a file here
    # data = unquote_plus(data)
    # print(data)
    if not url:
        return "No data"
    else:
        result = com(url, placeholder, args)
        result = json.loads(result)
        return result

@app.get('/compare') # usage : http://127.0.0.1:8001/compare?ship1=761&ship2=752
async def compare(request: Request):
    query = request.query_params
    # get data from url
    ship1 = query["ship1"]
    ship2 = query["ship2"]

    placeholder = "placeholder" # we do not output a file here
    # data = unquote_plus(data)
    # print(data)
    if not ship1 or not ship2:
        return "Missing ship id"
    else:
        result = compare_ships(ship1, ship2)
        result = json.loads(result)
        return result

@app.post('/analyze') # get a url
async def analyzepost(request: Request):
    request_json = await request.json()
    # convert request_json string to dict
    data_json = json.loads(request_json)
    json_args = data_json['args']
    json_image = data_json['image']
    
    args = {}
    query_keys = ["draw", "flip_vectors", "draw_all_com", "draw_all_cot", "draw_cot", "draw_com", "boost", "analyze"]

    for key in query_keys:
        if key in json_args:
            args[key] = json_args[key]
            
    # print(args)
    if not json_image:
        return "No data"
    else:
        url = json_image
        placeholder = "placeholder"
        result = com(url, placeholder, args)
        result = json.loads(result)
        # print(result)
        return result
    
    

app.add_middleware(SessionMiddleware, secret_key=os.getenv("secret_session"))
app.add_middleware(GZipMiddleware, minimum_size=1000)

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8001)
    # uvicorn.run(app)

    