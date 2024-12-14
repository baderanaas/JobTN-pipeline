import os
import re
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
import PyPDF2
import numpy as np
import ollama
from pymongo import MongoClient
import math
from tokenizers import Tokenizer
from chonkie import TokenChunker
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mongodb_uri = "mongodb://host.docker.internal:27017/"
mongodb_uri = "mongodb://localhost:27017/"
client = MongoClient(mongodb_uri)
db = client["embeddings_db"]
collection = db["job_embeddings"]

openai_api_key = os.getenv("OPENAI_API_KEY")
clientOpenAI = OpenAI(api_key=openai_api_key)

tokenizer = Tokenizer.from_pretrained("gpt2")
chunker = TokenChunker(tokenizer)

MAX_FILE_SIZE = 10 * 1024 * 1024

try:
    ollama.pull("llama3.1")
except Exception as e:
    print(f"Error pulling Ollama models: {e}")
    print("Ensure Ollama server is running")


def extract_text_from_pdf(pdf_file):
    print("extract text from pdf file")
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


def get_ada_embeddings(text: str):
    response = (
        clientOpenAI.embeddings.create(model="text-embedding-ada-002", input=[text])
        .data[0]
        .embedding
    )
    return response


def sections_top_matches(cv, k=5):
    print("getting top matches")

    embeddings = get_ada_embeddings(cv)

    embeddings_magnitude = math.sqrt(sum(x * x for x in embeddings))
    print("Embeddings magnitude:", embeddings_magnitude)

    current_time = datetime.utcnow()
    current_time = current_time.strftime("%Y-%m-%d")

    pipeline = [
        {"$match": {"expiration_date": {"$gt": current_time}}},
        {
            "$addFields": {
                "dotProduct": {
                    "$sum": {
                        "$map": {
                            "input": {"$zip": {"inputs": ["$embedding", embeddings]}},
                            "as": "pair",
                            "in": {
                                "$multiply": [
                                    {"$arrayElemAt": ["$$pair", 0]},
                                    {"$arrayElemAt": ["$$pair", 1]},
                                ]
                            },
                        }
                    }
                },
                "cosineSimilarity": {
                    "$cond": {
                        "if": {
                            "$and": [
                                {"$gt": ["$magnitudeJob", 0]},
                                {"$gt": [embeddings_magnitude, 0]},
                            ]
                        },
                        "then": {
                            "$divide": [
                                "$dotProduct",
                                {"$multiply": ["$magnitudeJob", embeddings_magnitude]},
                            ]
                        },
                        "else": 0,
                    }
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "job_string": {
                    "$concat": [
                        "link: ",
                        {"$ifNull": ["$link", "N/A"]},
                        ", company: ",
                        {"$ifNull": ["$company", "N/A"]},
                        ", title: ",
                        {"$ifNull": ["$title", "N/A"]},
                        ", workplace: ",
                        {"$ifNull": ["$workplace", "N/A"]},
                        ", expiration_date: ",
                        {"$toString": "$expiration_date"},
                        ", description: ",
                        {"$ifNull": ["$description", "N/A"]},
                        ", cosineSimilarity: ",
                        {"$toString": "$cosineSimilarity"},
                    ]
                },
                "cosineSimilarity": 1,
            }
        },
        {"$sort": {"cosineSimilarity": -1}},
        {"$limit": k},
    ]

    try:
        matches = list(collection.aggregate(pipeline, allowDiskUse=True))
        return matches
    except Exception as e:
        print(f"Error in finding matches: {e}")
        import traceback

        traceback.print_exc()

    return []


def formulate_response(resume):
    # sections = get_resume_sections(resume)
    top_matches = sections_top_matches(resume)
    prompt = f"""You are an expert job matcher and resume analyzer. Your task is to format job match information into a clear, concise response.

For each job match, follow these rules:
1. Start with the job title and company
2. Include the workplace type
3. Provide a concise summary of the job description (2-3 sentences)
4. Extract any contact information from the description
5. Include the job link at the end

Examples:

Example 1:
Input: 
link: https://careers.techgiant.com/job/123, 
company: Google, 
title: Senior Software Engineer, 
workplace: Hybrid, Tunisia, 
description: We are seeking a talented software engineer with expertise in machine learning and cloud computing. The ideal candidate will work on cutting-edge AI projects. Strong Python and TensorFlow skills required. Contact our recruiting team at recruit@google.com or call (650) 555-1234.

Output:
Senior Software Engineer at Google
Workplace: Hybrid, Tunisia
Google is seeking an experienced software engineer specializing in machine learning and cloud computing. The role focuses on developing innovative AI projects and requires strong Python and TensorFlow skills. Candidates will work on cutting-edge technology solutions.
Contact: recruit@google.com, (650) 555-1234
https://careers.techgiant.com/job/123

Example 2:
Input:
link: https://startup.jobs/engineering/456, 
company: TechInnovate Startup, 
title: Full Stack Developer, 
workplace: Remote, 
description: Exciting opportunity for a full stack developer to join our growing startup. Must have experience with React, Node.js, and PostgreSQL. We're building revolutionary financial technology solutions. Reach out to careers@techinnovate.io if interested.

Output:
Full Stack Developer at TechInnovate Startup
Workplace: Remote
TechInnovate Startup is seeking a full stack developer to contribute to their innovative financial technology solutions. The role requires expertise in React, Node.js, and PostgreSQL. Ideal for developers passionate about building cutting-edge tech products.
Contact: careers@techinnovate.io
https://startup.jobs/engineering/456

Now, process the following job match:
{top_matches}
"""

    response = ollama.generate(model="llama3.1", prompt=prompt)
    return response["response"]


@app.post("/match-jobs/")
async def match_jobs(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, detail="Invalid file format. Only PDFs are supported."
        )

    if file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large.")

    resume_bytes = BytesIO(await file.read())
    resume_text = extract_text_from_pdf(resume_bytes)

    # Match jobs
    try:
        job_matches = formulate_response(resume_text)
        return {"job_matches": job_matches}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing resume: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
