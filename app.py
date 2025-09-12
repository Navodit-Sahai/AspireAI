import streamlit as st
import os
from scrape import get_jobs_from_remoteok
from match_resume import analyze_resume_for_job
from urllib.parse import quote

# Import your LLM and PromptTemplate for cold email generation
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

# Initialize LLM once
llm = ChatGroq(model='llama3-70b-8192', max_retries=2)

def generate_email_for_job(job: dict, resume_text: str) -> str:
    prompt = PromptTemplate.from_template("""
        You are an enthusiastic job seeker applying for a new opportunity.
        Using the job description and your resume below, write a professional and personalized cold email 
        to the hiring manager expressing your interest in the role and highlighting how your skills align with their needs.

        Make the email polite, concise, and confident. Mention the job title and show genuine interest in the company.
        Avoid fluff. Do not write any preamble.

        ### JOB TITLE:
        {job_title}

        ### COMPANY:
        {company}

        ### JOB DESCRIPTION:
        {job_description}

        ### YOUR RESUME:
        {resume_text}

        ### EMAIL (No preamble):
        """)
    chain = prompt | llm
    res = chain.invoke({
        "job_title": job.get("title", "N/A"),
        "company": job.get("company", "N/A"),
        "job_description": job.get("job_posting", "N/A"),
        "resume_text": resume_text
    })
    return res.content

def read_resume_text(resume_path):
    with open(resume_path, "r", encoding="utf-8") as f:
        return f.read()

st.set_page_config(page_title="Job Listings App", layout="wide")
st.title("📄 Job Listings with Resume Analysis")

location = st.text_input("Enter job location", value="")
job_post = st.text_input("Enter job keyword/title", value="")

resume_file = st.file_uploader("Upload your resume (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"])

if "resume_path" not in st.session_state:
    st.session_state.resume_path = None
if "job_listings" not in st.session_state:
    st.session_state.job_listings = []
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = {}
if "generated_emails" not in st.session_state:
    st.session_state.generated_emails = {}

if resume_file:
    file_ext = os.path.splitext(resume_file.name)[1].lower()
    resume_path = "temp_resume" + file_ext
    with open(resume_path, "wb") as f:
        f.write(resume_file.getbuffer())
    st.session_state.resume_path = resume_path

if st.button("🔍 Search Jobs"):
    if not location or not job_post:
        st.error("Please enter both location and job keyword to search jobs.")
    else:
        job_listings = get_jobs_from_remoteok(location, job_post)
        if not job_listings:
            st.warning("No jobs found for your query.")
        else:
            st.session_state.job_listings = job_listings
            st.session_state.analysis_results = {}
            st.session_state.generated_emails = {}

if st.session_state.job_listings:
    st.subheader(f"✅ Jobs found for '{job_post}' in '{location}':")

    for idx, job in enumerate(st.session_state.job_listings):
        with st.container():
            st.markdown(f"### {job.get('title', 'N/A')} at {job.get('company', 'N/A')} ({job.get('location', 'N/A')})")
            st.markdown(f"**Job Description:** {job.get('job_posting', 'N/A')}")
            col1, col2, col3 = st.columns(3)

            if col1.button("📊 Resume Analysis", key=f"analyze_{idx}"):
                if not st.session_state.resume_path:
                    st.error("Please upload your resume first.")
                else:
                    result = analyze_resume_for_job(
                        st.session_state.resume_path,
                        job.get('job_posting', '')
                    )
                    st.session_state.analysis_results[idx] = result

            if idx in st.session_state.analysis_results:
                st.markdown("#### Resume Analysis Result:")
                st.json(st.session_state.analysis_results[idx])

            if col2.button("✉️ Generate Cold Email", key=f"email_{idx}"):
                if not st.session_state.resume_path:
                    st.error("Please upload your resume first.")
                else:
                    with st.spinner("Generating cold email..."):
                        resume_text = read_resume_text(st.session_state.resume_path)
                        email_text = generate_email_for_job(job, resume_text)
                        st.session_state.generated_emails[idx] = email_text

            if idx in st.session_state.generated_emails:
                st.markdown("#### Generated Cold Email:")
                st.code(st.session_state.generated_emails[idx], language="markdown")

            if col3.button("🤖 Mock Interview", key=f"interview_{idx}"):
                if st.session_state.resume_path:
                    job_title = quote(job.get("title", ""))
                    job_desc = quote(job.get("job_posting", ""))
                    resume_param = quote(st.session_state.resume_path)
                    INTERVIEW_BOT_URL = "http://localhost:8502"

                    interview_url = f"{INTERVIEW_BOT_URL}/?title={job_title}&desc={job_desc}&resume={resume_param}"

                    st.markdown(f"[Open Interview Bot for this job]( {interview_url} )", unsafe_allow_html=True)
                else:
                    st.error("Please upload your resume first.")

            st.markdown("---")
else:
    st.info("Search for jobs to see listings here.")
