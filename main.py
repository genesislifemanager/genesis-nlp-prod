from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from joblib import load
from pydantic import BaseModel

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
    "https://genesis-frontend-dev.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Query(BaseModel):
    uid: str
    query: str


def classifyQuery(query):
    model = load('./model/model.joblib')
    fitted_vectorizer = load('./model/fitted_vectorizer.joblib')
    typeId, = model.predict(fitted_vectorizer.transform([query]))

    if typeId == 0:    
        return "Task"
    if typeId == 1:
        return "Event"
    if typeId == 2:
        return "Routine"
    if typeId ==  3:
        return "Project"
    if typeId == 4:
        return "Venture"


def extractEntities(query):
    pass


@app.post("/query")
async def createQuery(query: Query):
    extracted=extractEntities(query.query)
    return {"status": "success", "data": {"uid": query.uid, "name": "", "type": classifyQuery(query.query), "mode": "", "s": "", "duration": "", "projectId": "", "reminder": "", "status": ""}}
