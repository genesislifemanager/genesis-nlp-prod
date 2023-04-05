import platform
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from joblib import load
from pydantic import BaseModel
import spacy
from spacy.matcher import Matcher
import re
from datetime import datetime

# I want to @study client server architecture@ module at 8.30 pm for 2 hours

nlp = spacy.load('en_core_web_sm')

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
    if typeId == 3:
        return "Project"
    if typeId == 4:
        return "Venture"


def extractName(query,entities_dict):

    # Define the regular expression pattern
    pattern = r'@\w+(?:\s+\w+)*@'

    # Find all matches of the regular expression in the text input
    matches = re.findall(pattern, query)

    # Loop through the matches and extract the words between the "@" signs
    for match in matches:
        # Remove the "@" signs and any leading or trailing whitespace
        words = match.strip('@').strip()

        # Tokenize the words using Spacy
        words_doc = nlp(words)

        list = [token.text for token in words_doc]
        output_string = ' '.join(list)
        entities_dict['name'] = output_string


def extractEntities(query, type):
    doc = nlp(query)
    start_time = None

    entities_dict = {}
    duration_entities = {}
    token_check_min="minutes"
    token_check_hour="hours"
    token1 = nlp(token_check_min)[0]
    token2=nlp(token_check_hour)[0]

    if (type == "Task") or (type == "Event") or (type == "Routine"):

        extractName(query,entities_dict)
        duration_hours=""
        duration_minutes=""

        for token in doc:
            # Check if the token is a number
            if token.pos_ == "NUM":
                # Check if the next token is "pm" or "am"
                next_token = doc[token.i+1] if token.i+1 < len(doc) else None
                if not start_time:
                    # This is the start time
                    start_time = token.text + " " + next_token.text
                    time_obj = datetime.strptime(start_time, '%I.%M %p')
                    time_24_str = time_obj.strftime('%H:%M')
                    entities_dict['s'] = time_24_str

                   # print("Start time:", start_time)

                if next_token and (next_token.text == "hours"):
                        duration_hours = str(token.text)
                        #print(duration_hours)
                        if token1 in doc:
                                for token in doc:
                                        if next_token and (next_token.text == "minutes"):
                                                duration_minutes=str(token.text)
                                        else:
                                            duration_minutes=0
                       

                

                if next_token and (next_token.text == "minutes"):
                       duration_minutes=str(token.text)
                       if token2 in doc:
                                for token in doc:
                                        if next_token and (next_token.text == "hours"):
                                                duration_hours=str(token.text)
                                        else:
                                            duration_hours=0


        duration_entities['h']=duration_hours
        duration_entities['m']=duration_minutes
        entities_dict['duration']=duration_entities
                                       

    ''''elif next_token and (next_token.text == "hours"):
                    # The number is part of a duration expression
                    duration_hours = str(token.text)
                    entities_dict['duration'] = duration_hours+" hours"
                    duration_entities['h'] = duration_hours
                    duration_entities['m'] = 0
                    entities_dict['duration'] = duration_entities

                # print("Duration:", duration, "hours")

                elif next_token and (next_token.text == "minutes"):
                    duration_minutes = str(token.text)
                    duration_entities['h'] = duration_hours
                    duration_entities['m'] = duration_minutes
                    entities_dict['duration'] = duration_entities'''

    if (type == "Project"):

        extractName(query,entities_dict)
        duration_hours=""
        duration_minutes=""

        pattern2 = r"\d{2}/\d{2}/\d{4}\s\d{2}:\d{2}"
        matches = re.findall(pattern2, query)
        entities_dict['due'] = matches[0]
        
        for token in doc:
        # Check if the token is a number
            if token.pos_ == "NUM":
                    next_token = doc[token.i+1] if token.i+1 < len(doc) else None
                    if next_token and (next_token.text == "hours"):
                            duration_hours = str(token.text)
                            #print(duration_hours)
                            if token1 in doc:
                                    for token in doc:
                                            if next_token and (next_token.text == "minutes"):
                                                    duration_minutes=str(token.text)
                                            else:
                                                duration_minutes=0
                        

                    

                    if next_token and (next_token.text == "minutes"):
                        duration_minutes=str(token.text)
                        if token2 in doc:
                                    for token in doc:
                                            if next_token and (next_token.text == "hours"):
                                                    duration_hours=str(token.text)
                                            else:
                                                duration_hours=0

        duration_entities['h']=duration_hours
        duration_entities['m']=duration_minutes
        entities_dict['duration']=duration_entities   

    


    if (type == "Venture"):

        extractName(query,entities_dict)

    return entities_dict


@app.post("/query")
async def createQuery(query: Query):
    type = classifyQuery(query.query)
    print(type)
    extracted = {}
    try:
        extracted = extractEntities(query.query, type)
        print(extracted)
    except:
         return {"status": "fail", "data": {"uid": query.uid}}
    
    if (type == "Task") or (type == "Event") or (type == "Routine"):
        return {"status": "success", "data": {"uid": query.uid, "name": extracted["name"], "type": type, "mode": "Static", "s": extracted["s"], "duration": extracted["duration"], "projectId": -1, "reminder": "", "status": "Open"}}
    
    elif type == "Project":
        return {"status": "success", "data": {"uid": query.uid, "name": extracted["name"], "due":extracted["due"], "duration": extracted["duration"], "ventureId": -1, "status": "Open"}}

    elif type == "Venture":
        return {"status": "success", "data": {"uid": query.uid, "name": extracted["name"]}}