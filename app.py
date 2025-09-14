import streamlit as st
import os
from scrape import get_jobs_from_remoteok
from match_resume import analyze_resume_for_job
from urllib.parse import quote
from datetime import datetime

# Import your LLM and PromptTemplate for cold email generation
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

# Import mock interview functions - Fixed imports
from interview.speech_to_text import record_audio, transcribe_with_groq
# Updated imports to match your file structure
from interview.conversation import take_interview, sanitize_content
from interview.captool import analyze_image_with_query
from interview.text_to_speech import text_to_speech_with_gtts

import threading
import time

# Initialize LLM once
llm = ChatGroq(model_name="llama-3.3-70b-versatile")

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

def read_resume_file(resume_path):
    """Read resume content from file"""
    try:
        with open(resume_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading resume: {str(e)}"

def play_audio_async(text):
    """Play audio in a separate thread"""
    def play_audio():
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_file = f"temp_audio_{timestamp}.mp3"
            text_to_speech_with_gtts(text, audio_file)
                
            time.sleep(2)
            if os.path.exists(audio_file):
                os.remove(audio_file)
        except Exception as e:
            st.error(f"Audio playback error: {str(e)}")
    
    thread = threading.Thread(target=play_audio)
    thread.daemon = True
    thread.start()

def get_vision_context():
    """Get vision context from camera"""
    try:
        query = "Analyze this person during interview: body language, confidence, eye contact, appearance. Keep brief."
        return analyze_image_with_query(query)
    except Exception as e:
        return f"Vision unavailable: {str(e)}"

def run_mock_interview(job, resume_path):
    """Run mock interview in the same app"""
    st.markdown("---")
    st.markdown("## 🤖 Mock Interview Session")
    
    job_title = job.get("title", "Software Engineer")
    job_description = job.get("job_posting", "No job description provided")
    
    # Initialize interview session state
    interview_key = f"interview_{job.get('title', 'default')}"
    
    if f"{interview_key}_started" not in st.session_state:
        st.session_state[f"{interview_key}_started"] = False
    if f"{interview_key}_conversation" not in st.session_state:
        st.session_state[f"{interview_key}_conversation"] = []
    if f"{interview_key}_current_question" not in st.session_state:
        st.session_state[f"{interview_key}_current_question"] = ""
    if f"{interview_key}_ended" not in st.session_state:
        st.session_state[f"{interview_key}_ended"] = False
    if f"{interview_key}_resume_text" not in st.session_state:
        st.session_state[f"{interview_key}_resume_text"] = ""
    
    # Load resume
    if resume_path and not st.session_state[f"{interview_key}_resume_text"]:
        st.session_state[f"{interview_key}_resume_text"] = read_resume_file(resume_path)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"**Position:** {job_title}")
        st.markdown(f"**Company:** {job.get('company', 'N/A')}")
    
    with col2:
        if st.button("🔄 Reset Interview", key=f"reset_{interview_key}"):
            st.session_state[f"{interview_key}_started"] = False
            st.session_state[f"{interview_key}_conversation"] = []
            st.session_state[f"{interview_key}_current_question"] = ""
            st.session_state[f"{interview_key}_ended"] = False
            st.rerun()
        
        if st.button("❌ Close Interview", key=f"close_{interview_key}"):
            # Clear all interview session state
            keys_to_remove = [key for key in st.session_state.keys() if interview_key in key]
            for key in keys_to_remove:
                del st.session_state[key]
            st.session_state.active_interview = None
            st.rerun()
    
    if not st.session_state[f"{interview_key}_started"]:
        st.markdown("### 🚀 Ready to Start Your Mock Interview?")
        st.info("Click the button below to begin your AI-powered mock interview!")
        st.warning("⚠️ Make sure your camera and microphone are working and permissions are granted.")
        
        if st.button("🎤 Start Interview", type="primary", key=f"start_{interview_key}"):
            st.session_state[f"{interview_key}_started"] = True
            
            with st.spinner("Preparing your interview..."):
                try:
                    vision_context = get_vision_context()
                    
                    interviewer_response = take_interview(
                        job_title, 
                        job_description, 
                        st.session_state[f"{interview_key}_resume_text"],
                        vision_context
                    )
                    
                    question = sanitize_content(interviewer_response)
                    st.session_state[f"{interview_key}_current_question"] = question
                    st.session_state[f"{interview_key}_conversation"].append({
                        "role": "interviewer",
                        "content": question,
                        "timestamp": datetime.now()
                    })
                    
                    play_audio_async(question)
                    st.success("✅ Interview started! Listen to the question and record your answer.")
                    
                except Exception as e:
                    st.error(f"Error starting interview: {str(e)}")
                    st.session_state[f"{interview_key}_started"] = False
            st.rerun()
    
    else:
        if not st.session_state[f"{interview_key}_ended"]:
            st.markdown("### 🎯 Interview in Progress")
            
            # Display current question
            if st.session_state[f"{interview_key}_current_question"]:
                st.markdown("#### 🤖 Interviewer:")
                st.info(st.session_state[f"{interview_key}_current_question"])
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🎤 Record Answer", type="primary", key=f"record_{interview_key}"):
                    with st.spinner("🎙️ Recording... Speak now!"):
                        try:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            audio_file = f"temp_recording_{timestamp}.mp3"
                            
                            record_audio(audio_file, timeout=30, phrase_time_limit=30)
                            candidate_response = transcribe_with_groq(audio_file)
                            
                            if candidate_response:
                                st.session_state[f"{interview_key}_conversation"].append({
                                    "role": "candidate",
                                    "content": candidate_response,
                                    "timestamp": datetime.now()
                                })
                                
                                st.success("✅ Response recorded!")
                                st.write(f"**Your response:** {candidate_response}")
                            else:
                                st.warning("Could not transcribe your response. Please try again.")
                            
                            if os.path.exists(audio_file):
                                os.remove(audio_file)
                                
                        except Exception as e:
                            st.error(f"Recording error: {str(e)}")
            
            with col2:
                if st.button("⭐ Get Next Question", key=f"next_{interview_key}"):
                    conversation = st.session_state[f"{interview_key}_conversation"]
                    if conversation and conversation[-1]["role"] == "candidate":
                        
                        with st.spinner("🤔 Generating next question..."):
                            try:
                                vision_context = get_vision_context()
                                
                                conversation_context = "\n".join([
                                    f"{msg['role'].title()}: {msg['content']}" 
                                    for msg in conversation[-3:]
                                ])
                                
                                full_context = f"Previous conversation:\n{conversation_context}\n\nVision: {vision_context}"
                                
                                interviewer_response = take_interview(
                                    job_title,
                                    job_description,
                                    st.session_state[f"{interview_key}_resume_text"],
                                    full_context
                                )
                                
                                response_content = sanitize_content(interviewer_response)
                                
                                if "This concludes our interview" in response_content:
                                    st.session_state[f"{interview_key}_ended"] = True
                                
                                st.session_state[f"{interview_key}_current_question"] = response_content
                                st.session_state[f"{interview_key}_conversation"].append({
                                    "role": "interviewer",
                                    "content": response_content,
                                    "timestamp": datetime.now()
                                })
                                
                                play_audio_async(response_content)
                            except Exception as e:
                                st.error(f"Error generating question: {str(e)}")
                        st.rerun()
                    else:
                        st.warning("Please record an answer first!")
            
            with col3:
                if st.button("🛑 End Interview", key=f"end_{interview_key}"):
                    st.session_state[f"{interview_key}_ended"] = True
                    st.rerun()
        
        else:
            st.markdown("### ✅ Interview Completed!")
            st.success("Thank you for completing the mock interview!")
            
            if st.session_state[f"{interview_key}_current_question"]:
                st.info(st.session_state[f"{interview_key}_current_question"])
        
        # Show conversation history
        conversation = st.session_state[f"{interview_key}_conversation"]
        if conversation:
            with st.expander("📝 Interview Transcript"):
                for msg in conversation:
                    role_emoji = "🤖" if msg["role"] == "interviewer" else "👤"
                    st.write(f"{role_emoji} **{msg['role'].title()}:** {msg['content']}")

# Main Streamlit App
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
if "active_interview" not in st.session_state:
    st.session_state.active_interview = None

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
        with st.spinner("Searching for jobs..."):
            job_listings = get_jobs_from_remoteok(location, job_post)
            if not job_listings:
                st.warning("No jobs found for your query.")
            else:
                st.session_state.job_listings = job_listings
                st.session_state.analysis_results = {}
                st.session_state.generated_emails = {}
                st.success(f"Found {len(job_listings)} jobs!")

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
                    with st.spinner("Analyzing resume..."):
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
                    st.session_state.active_interview = idx
                    st.rerun()
                else:
                    st.error("Please upload your resume first.")

            st.markdown("---")
    
    # Display active interview
    if st.session_state.active_interview is not None:
        active_job = st.session_state.job_listings[st.session_state.active_interview]
        run_mock_interview(active_job, st.session_state.resume_path)

else:
    st.info("Search for jobs to see listings here.")