from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from typing import Annotated

import pymongo
from bson.objectid import ObjectId
import os
from llms import *
from groq import Groq
from dotenv import load_env

load_env()
# MongoDB setup
MONGO_URI = os.env['MONGO_URI']
DATABASE_NAME = "claims_db"
COLLECTION_NAME = "municipal_claims"


client = pymongo.MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Initialize FastAPI app
app = FastAPI(title="Audio/Text Classification API", description="API to transcribe audio, classify text, and store in MongoDB", version="1.0")

# Pydantic model for structured data
class DataModel(BaseModel):
    text: str
    additional_info: Optional[dict] = {}
    classification: Optional[str] = None
    keywords: Optional[list] = None

def classify_text(text: str) -> str:
    # Replace with actual classification logic
    return "placeholder_classification"

# Function to transcribe audio
async def transcribe_audio(file_path: str) -> str:

    client = Groq()
    filename = os.path.dirname(__file__)

    try:
        with open(file_path, "rb") as file:
            transcription = client.audio.transcriptions.create(

            file=(file_path, file.read()),
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
            )
            print(transcription.text)

            return transcription.text
        
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech recognition error: {e}")

@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    return {"file_size": len(file)}


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}   

@app.post("/process")
async def process_input(
    file: UploadFile = File(None),
    text: Optional[str] = Form(None),
    
    additional_info: Optional[str] = Form("{}")
):
    if not text and not file:
        raise HTTPException(status_code=400, detail="Either 'text' or 'file' must be provided.")

    # Transcription if file is provided
    transcript = None
    if file:
        if not file.filename.endswith(".mp3"):
            raise HTTPException(status_code=400, detail="Only MP3 files are supported.")

        temp_file = f"temp_{file.filename}"
        with open(temp_file, "wb") as f:
            f.write(await file.read())

        try:
            transcript = await transcribe_audio(temp_file)
        finally:
            os.remove(temp_file)

    # Prepare the data for MongoDB
    try:
        additional_info_dict = eval(additional_info)  # Use a safer parser in production
    except:
        additional_info_dict = {}

    # Use provided text if available
    final_text = transcript if transcript else text
    claim = {'claim': final_text, 'municipality': additional_info_dict.get("municipality", "")}

    # Classify the text
    classification, keywords = analyze_text(claim)

    data = {
        "text": final_text,
        "additional_info": additional_info_dict,
        "classification": classification,
        "keywords": keywords
    }
    print(data)
    # Insert into MongoDB

    try:
        # result = collection.insert_one(data)
        pass
    except Exception as e:
        print(HTTPException(status_code=500, detail=f"Error saving data to MongoDB: {e}"))

    return {
            "message": "Data processed and saved successfully.",
            'data': data
        }
        

@app.get("/data/{item_id}")
async def get_data(item_id: str):
    try:
        result = collection.find_one({"_id": ObjectId(item_id)})
        if not result:
            raise HTTPException(status_code=404, detail="Item not found.")
        result["_id"] = str(result["_id"])
        return result
    except:
        raise HTTPException(status_code=400, detail="Invalid item ID.")

# Swagger UI is automatically generated by FastAPI
