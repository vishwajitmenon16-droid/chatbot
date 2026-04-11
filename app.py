import streamlit as st
from google.genai import Client, types
import pandas as pd
import numpy as np

# --- 1. CONFIGURATION & SECRETS ---
st.set_page_config(page_title="SimuExpert Pro", layout="wide", page_icon="🧪")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client = Client(api_key=API_KEY)
except Exception:
    st.error("🔑 API Key missing! Add 'GEMINI_API_KEY' to Streamlit Secrets.")
    st.stop()

# --- 2. SESSION STATE FOR HISTORY ---
# We store 'history' as a dictionary where keys are Project Names
if "history" not in st.session_state:
    st.session_state.history = {}

if "current_project" not in st.session_state:
    st.session_state.current_project = "New Project"

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. SIDEBAR: PROJECT HISTORY ---
with st.sidebar:
    st.title("📚 Chat History")
    
    # Button to start a fresh project
    if st.button("➕ New Project", use_container_width=True):
        # Save old project before clearing if it has messages
        if st.session_state.messages:
            project_name = st.session_state.messages[0]["content"][:30] + "..."
            st.session_state.history[project_name] = st.session_state.messages
        
        st.session_state.messages = []
        st.session_state.current_project = "New Project"
        st.rerun()

    st.markdown("---")
    st.subheader("Previous Simulations")
    
    # List all saved history
    for project_name in list(st.session_state.history.keys()):
        if st.button(project_name, key=project_name, use_container_width=True):
            st.session_state.messages = st.session_state.history[project_name]
            st.session_state.current_project = project_name
            st.rerun()

# --- 4. THE ENGINEERING BRAIN ---
SYSTEM_INSTRUCTION = (
    "You are a Senior Simulation Engineer. For every query:\n"
    "1. SOLVE & EXPLAIN: Use LaTeX for equations.\n"
    "2. THE IN, PROCESS, and OUT: Break down the theory, modeling, and results.\n"
    "Target: 3rd-year VIT Engineering student."
)

# --- 5. MAIN CHAT UI ---
st.title(f"🧪 {st.session_state.current_project}")
st.caption("Access your previous projects from the sidebar.")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. CHAT LOGIC ---
if prompt := st.chat_input("Ask a simulation question..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Gemini is thinking..."):
            try:
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION
                    )
                )
                
                full_response = response.text
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                # Auto-update project name based on first question
                if st.session_state.current_project == "New Project":
                    new_name = prompt[:30] + "..."
                    st.session_state.current_project = new_name
                    st.session_state.history[new_name] = st.session_state.messages
                    st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")
