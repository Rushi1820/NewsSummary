from fastapi import FastAPI, Request
import uvicorn
import api
import requests


app=FastAPI()


app.include_router(api.router, prefix="/api/v1", tags=["Company News"])

@app.middleware("http")
async def log_request_body(request: Request, call_next):
     body = await request.body()
     response = await call_next(request)
     return response

if __name__=="__main__":
    uvicorn.run("main:app",host="127.0.0.1",port=8080)