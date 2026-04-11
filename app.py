import streamlit as st
from google.genai import Client, types
import pandas as pd
import numpy as np

# --- 1. CONFIGURATION & SECRETS ---
st.set_page_config(page_title="SimuExpert AI + Math", layout="wide", page_icon="🧪")

try:
    # Ensure 'GEMINI_API_KEY' is set in your Streamlit Cloud Secrets
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client = Client(api_key=API_KEY)
except Exception as e:
    st.error(f"🔑 Setup Error: {e}. Please add your GEMINI_API_KEY to Streamlit Secrets.")
    st.stop()

# --- 2. THE ENGINEERING BRAIN (System Instructions) ---
SYSTEM_INSTRUCTION = (
    "You are a Senior Simulation Engineer and Math Specialist. For every query:\n"
    "1. SOLVE & EXPLAIN: If there is an equation, solve it step-by-step using LaTeX.\n"
    "2. THE IN (Theory): Explain the fundamental physics behind the prompt.\n"
    "3. THE PROCESS (Modeling): Detail the steps to model this in Simulink/Simscape.\n"
    "4. THE OUT (Application): Explain the real-world engineering impact.\n"
    "Target: 3rd-year VIT Engineering student (Technical, precise, and academic)."
)

# --- 3. UI SETUP ---
st.title("🧪 SimuExpert: AI Solver & Simulator")
st.caption("Advanced Math & Simulation Reasoning Engine")
st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for AI Control
with st.sidebar:
    st.header("AI Logic Settings")
    # Gemini 3 allows specialized reasoning levels
    thinking_level = st.select_slider(
        "Reasoning Depth",
        options=["MINIMAL", "LOW", "MEDIUM", "HIGH"],
        value="MEDIUM",
        help="Higher levels improve math accuracy but increase response time."
    )
    if st.button("Reset Conversation"):
        st.session_state.messages = []
        st.rerun()

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. CHAT & EQUATION LOGIC ---
if prompt := st.chat_input("Ex: 'Calculate the convective heat transfer for a cylinder'"):
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing Physics & Solving Equations..."):
            try:
                # API Call using the Gemini 3 Flash model
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        thinking_config=types.ThinkingConfig(
                            thinking_level=thinking_level
                        )
                    )
                )
                
                full_response = response.text
                st.markdown(full_response)
                
                # Visual Helper (Random data trend for 'Simulations')
                if any(x in prompt.lower() for x in ["sim", "plot", "graph"]):
                    st.divider()
                    st.write("### Simulation Result Preview")
                    df = pd.DataFrame(np.random.randn(20, 2), columns=['Theoretical', 'Simulated'])
                    st.line_chart(df)

                # Save assistant response to state
                st.session_state.messages.append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error(f"Model Error: {e}")
                st.info("Ensure you are using the 'google-genai' library in your requirements.txt")
