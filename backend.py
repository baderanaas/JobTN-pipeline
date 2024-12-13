import os
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
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

try:
    ollama.pull("llama3.1")
except Exception as e:
    print(f"Error pulling Ollama models: {e}")
    print("Ensure Ollama server is running")


def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


def get_resume_sections(resume):
    prompt = f"""Parse the following resume into clear, standard sections. Use only the sections that are actually present in the resume. Separate each section with ** and ensure the section names are in all uppercase.

Example 1:
---
John Smith
123 Main Street | john.smith@email.com | (555) 123-4567

PROFESSIONAL SUMMARY
Experienced marketing professional with 5+ years of digital marketing expertise.

WORK EXPERIENCE
Senior Marketing Specialist, Tech Innovations Inc. (2020-2023)
- Led digital marketing campaigns
- Increased online engagement by 40%

EDUCATION
Bachelor of Science in Marketing, State University, 2019

SKILLS
- Digital Marketing
- SEO
- Social Media Management
---
Output:
PROFESSIONAL SUMMARY: Experienced marketing professional with 5+ years of digital marketing expertise.**WORK EXPERIENCE: Senior Marketing Specialist, Tech Innovations Inc. (2020-2023)
- Led digital marketing campaigns
- Increased online engagement by 40%**EDUCATION: Bachelor of Science in Marketing, State University, 2019**SKILLS: - Digital Marketing
- SEO
- Social Media Management

Example 2:
---
Jane Doe
jane.doe@email.com | (555) 987-6543

SUMMARY
Innovative software engineer with expertise in full-stack development.

TECHNICAL SKILLS
- Python
- JavaScript
- React
- AWS

PROFESSIONAL EXPERIENCE
Software Engineer, Tech Solutions LLC (2018-2023)
- Developed scalable web applications
- Implemented microservices architecture

CERTIFICATIONS
AWS Certified Developer
---
Output:
SUMMARY: Innovative software engineer with expertise in full-stack development.**TECHNICAL SKILLS: - Python
- JavaScript
- React
- AWS**PROFESSIONAL EXPERIENCE: Software Engineer, Tech Solutions LLC (2018-2023)
- Developed scalable web applications
- Implemented microservices architecture**CERTIFICATIONS: AWS Certified Developer

Now, parse the following resume into sections:
{resume}
"""
    response = ollama.generate(model="llama3.1", prompt=prompt)

    return (response.message.content).split("**")


def get_ada_embeddings(text: str):
    response = (
        clientOpenAI.embeddings.create(model="text-embedding-ada-002", input=[text])
        .data[0]
        .embedding
    )
    return response


def sections_embeddings(sections):
    embeddings = []
    for section in sections:
        chunks = chunker(section)
        embeddings_list = [get_ada_embeddings(chunk) for chunk in chunks]
        embeddings.append(np.mean(embeddings_list, axis=0))
    return np.mean(embeddings, axis=0)


def get_top_matches(resume_embedding, k=5):
    resume_magnitude = math.sqrt(sum(x * x for x in resume_embedding))

    current_time = datetime.utcnow()

    pipeline = [
        {"$match": {"expiration_date": {"$gt": current_time}}},
        {
            "$addFields": {
                "dotProduct": {
                    "$reduce": {
                        "input": {"$zip": {"inputs": ["$embedding", resume_embedding]}},
                        "initialValue": 0,
                        "in": {
                            "$add": [
                                "$$value",
                                {"$multiply": ["$$this[0]", "$$this[1]"]},
                            ]
                        },
                    }
                }
            }
        },
        {
            "$addFields": {
                "cosineSimilarity": {
                    "$divide": [
                        "$dotProduct",
                        {"$multiply": ["$magnitudeJob", resume_magnitude]},
                    ]
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "job_string": {
                    "$concat": [
                        "link: ",
                        "$link",
                        ", company: ",
                        "$company",
                        ", title: ",
                        "$title",
                        ", workplace: ",
                        "$workplace",
                        ", expiration_date: ",
                        {"$toString": "$expiration_date"},
                        ", description: ",
                        "$description",
                    ]
                },
                "cosineSimilarity": 1,
            }
        },
        {"$sort": {"cosineSimilarity": -1}},
        {"$limit": k},
    ]

    try:
        top_matches = list(db.collection.aggregate(pipeline))
        return [match["job_string"] for match in top_matches]
    except Exception as e:
        print(f"Error in finding top matches: {e}")
        return []


def formulate_response(resume):
    sections = get_resume_sections(resume)
    resume_embedding = sections_embeddings(sections)
    top_matches = get_top_matches(resume_embedding)
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
"""

    response = ollama.generate(model="llama3.1", prompt=prompt)
    return response.message.content


@app.post("/match-jobs/")
async def match_jobs(file: UploadFile = File(...)):
    # Save the uploaded file temporarily
    with open("temp_resume.pdf", "wb") as buffer:
        buffer.write(await file.read())

    # Extract text from PDF
    resume_text = extract_text_from_pdf("temp_resume.pdf")

    # Remove temporary file
    os.remove("temp_resume.pdf")

    # Match jobs
    job_matches = formulate_response(resume_text)

    return {"job_matches": job_matches}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
