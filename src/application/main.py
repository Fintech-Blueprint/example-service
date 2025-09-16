from fastapi import FastAPI
import os


app = FastAPI()


@app.get('/healthz')
async def healthz():
    return {"status": "ok"}


@app.get('/v1/ping')
async def ping():
    commit = os.environ.get('COMMIT_SHA', 'dev')
    return {"pong": True, "service": "example-service", "commit": commit}
