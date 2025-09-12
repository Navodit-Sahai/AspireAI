from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
import os
from llm import llm
from langchain.prompts import PromptTemplate
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser

def resume_analysis(path: str):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        loader = PyPDFLoader(path)
    elif ext == ".docx":
        loader = Docx2txtLoader(path)
    elif ext == ".txt":
        loader = TextLoader(path)
    else:
        raise ValueError("Unsupported file format.")

    documents = loader.load()
    return "\n".join([doc.page_content for doc in documents])

class ResumeAnalysisResult(BaseModel):
    matching_percentage: int
    suggestions: list[str]

py_parser = PydanticOutputParser(pydantic_object=ResumeAnalysisResult)

template = """You are an expert career coach and resume reviewer.

Given the following inputs:

Resume Text:
{resume_text}

Job Posting Description:
{job_posting}

Your task is to:

1. Analyze how well the provided resume matches the requirements and skills mentioned in the job posting.
2. Calculate and provide a matching percentage score (0 to 100) indicating how closely the resume fits the job.
3. Provide specific, actionable suggestions to improve the resume so it aligns better with the job posting. Focus on skills, experience, keywords, and format improvements.

ONLY respond with a valid JSON object in this exact format:

{{
  "matching_percentage": 0,
  "suggestions": [
    "suggestion 1",
    "suggestion 2",
    "... more suggestions ..."
  ]
}}"""

def analyze_resume_for_job(resume_path, job_posting):
    resume_text = resume_analysis(resume_path)
    prompt_template = PromptTemplate(template=template, input_variables=['resume_text', 'job_posting'])
    prompt = prompt_template.format(resume_text=resume_text, job_posting=job_posting)

    response = llm.invoke(prompt)
    response_text = response.content  # get raw LLM output text

    try:
        parsed = py_parser.parse(response_text)
    except Exception as e:
        print("Parsing error:", e)
        print("Raw response was:", response_text)
        raise e

    return parsed
