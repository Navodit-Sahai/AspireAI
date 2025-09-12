import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.document_loaders import WebBaseLoader

load_dotenv()

llm = ChatGroq(model='llama3-70b-8192', max_retries=2)
parser = JsonOutputParser()

@st.cache_resource
def load_portfolio_df():
    csv_path = r"C:\Users\sahai\OneDrive\Desktop\GenAI proj\cold-email generator\my_portfolio.csv"
    df = pd.read_csv(csv_path, encoding='utf-8')
    return df

def extract_jobs_from_url(url):
    loader = WebBaseLoader(url)
    page_data = loader.load().pop().page_content

    prompt_extract = PromptTemplate.from_template("""
        ### SCRAPED TEXT FROM WEBSITE:
        {page_data}
        ### INSTRUCTION:
        The scraped text is from the career's page of a website.
        Your job is to extract the list of job postings and return them in JSON format containing the 
        following keys for each job: `role`, `experience`, `skills`, and `description`.
        Only return valid JSON (list of job dicts).
        ### VALID JSON (NO PREAMBLE):    
    """)

    chain_extract = prompt_extract | llm
    res = chain_extract.invoke({"page_data": page_data})
    jobs = parser.parse(res.content)
    return jobs  

def find_relevant_links(skills, portfolio_df, max_links=2):
    skills_lower = [skill.lower() for skill in skills] if isinstance(skills, list) else [skills.lower()]
    matched = portfolio_df[
        portfolio_df["Techstack"].str.lower().apply(
            lambda tech: any(skill in tech for skill in skills_lower)
        )
    ]
    links = matched["Links"].head(max_links).tolist()
    return links

def generate_email_for_job(job, resume_text, portfolio_df):
    relevant_links = find_relevant_links(job['skills'], portfolio_df)

    prompt_email = PromptTemplate.from_template("""
        ### JOB DESCRIPTION:
        {job_description}
        
        ### USER RESUME:
        {resume_text}
        
        ### INSTRUCTION:
        You are Mohan, a business development executive at AtliQ. AtliQ is an AI & Software Consulting company dedicated to facilitating
        the seamless integration of business processes through automated tools. 
        Over our experience, we have empowered numerous enterprises with tailored solutions, fostering scalability, 
        process optimization, cost reduction, and heightened overall efficiency. 
        Your job is to write a cold email to the client regarding the job mentioned above describing the capability of AtliQ 
        in fulfilling their needs.
        Also add the most relevant ones from the following links to showcase AtliQ's portfolio: {link_list}
        Remember you are Mohan, BDE at AtliQ. 
        Do not provide a preamble.
        ### EMAIL (NO PREAMBLE):
    """)

    chain_email = prompt_email | llm
    res = chain_email.invoke({
        "job_description": str(job),
        "resume_text": resume_text,
        "link_list": relevant_links
    })
    return res.content

