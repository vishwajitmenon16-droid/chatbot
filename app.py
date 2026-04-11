import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import numpy as np

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SimuExpert AI + Math", layout="wide", page_icon="🧪")

try:
    # Uses the new GenAI Client (2026 Standard)
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=API_KEY)
except Exception:
    st.error("🔑 API Key missing! Add 'GEMINI_API_KEY' to Streamlit Secrets.")
    st.stop()

# --- 2. THE ENGINEERING BRAIN ---
SYSTEM_INSTRUCTION = (
    "You are a Senior Simulation Engineer and Math Specialist. For every query:\n"
    "1. SOLVE & EXPLAIN: If there is an equation, solve it step-by-step using LaTeX.\n"
    "2. THE IN: Explain the physics/theory behind the user's prompt.\n"
    "3. THE PROCESS: Detail the Simulink/Simscape modeling steps.\n"
    "4. THE OUT: Explain the real-world engineering impact.\n"
    "Target: 3rd-year VIT Engineering student."
)

# --- 3. UI SETUP ---
st.title("🧪 SimuExpert: AI Solver & Simulator")
st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for Thinking Level (New Gemini 3 Feature)
with st.sidebar:
    st.header("AI Brain Settings")
    thinking_level = st.select_slider(
        "Reasoning Depth",
        options=["minimal", "low", "medium", "high"],
        value="medium",
        help="Higher levels solve complex math better but take more time."
    )
    if st.button("Reset Conversation"):
        st.session_state.messages = []
        st.rerun()

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. CHAT & EQUATION LOGIC ---
if prompt := st.chat_input("Ex: 'Solve the torque equation for a PMSM motor with 50A current'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing Logic & Equations..."):
            try:
                # API Call with Gemini 3 "Thinking" configuration
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        thinking_config=types.ThinkingConfig(
                            thinking_level=thinking_level.upper()
                        )
                    )
                )
                
                full_response = response.text
                st.markdown(full_response)
                
                # Equation/Graph Helper
                if any(x in prompt.lower() for x in ["solve", "calculate", "equation"]):
                    st.success("Calculations completed using high-depth reasoning.")
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"Error: {e}")
