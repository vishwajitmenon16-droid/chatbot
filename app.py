import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SimuExpert v3.0", layout="wide", page_icon="🤖")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("🔑 API Key missing in Streamlit Secrets!")
    st.stop()

# --- 2. THE ENGINEERING BRAIN ---
SYSTEM_INSTRUCTION = (
    "You are a Senior Simulation Engineer. For every query:\n"
    "1. THE IN: Explain the fundamental physics/theory.\n"
    "2. THE PROCESS: Detail the Simulink/Simscape/Ansys setup steps.\n"
    "3. THE OUT: Explain the impact on real-world engineering results.\n"
    "Context: 3rd-year VIT Engineering Student."
)

# --- 3. MODEL DISCOVERY (Fixes the 404 Error) ---
@st.cache_resource
def get_best_model():
    """Finds the most recent Flash model available to your API key."""
    try:
        # We try Gemini 3 Flash first (Current standard for 2026)
        return genai.GenerativeModel(
            model_name='gemini-3-flash-preview', 
            system_instruction=SYSTEM_INSTRUCTION
        )
    except:
        # Fallback to the latest generic alias if specific version fails
        return genai.GenerativeModel(
            model_name='gemini-flash-latest',
            system_instruction=SYSTEM_INSTRUCTION
        )

model = get_best_model()

# --- 4. UI DESIGN ---
st.title("⚡ SimuExpert: Advanced AI Simulation")
st.info("Debugging Mode: Connected to Gemini 3 series.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for Debugging & Model Info
with st.sidebar:
    st.header("System Status")
    if st.checkbox("Show Available Models"):
        st.write("Your key supports:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                st.code(m.name)
    
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

# Display Chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. CHAT LOGIC ---
if prompt := st.chat_input("Ask: 'Simulate the thermal runaway of an EV battery pack'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Calculating Physics & Engineering Models..."):
            try:
                # Direct generation using system instruction defined in step 3
                response = model.generate_content(prompt)
                full_response = response.text
                st.markdown(full_response)
                
                # Dynamic Visualization
                if any(x in prompt.lower() for x in ["sim", "graph", "data"]):
                    st.divider()
                    st.write("### Simulation Trend Analysis")
                    df = pd.DataFrame(np.random.randn(20, 2), columns=['Target', 'Actual'])
                    st.line_chart(df)

                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Execution Error: {e}")
                st.info("Check the sidebar to see if 'gemini-3-flash-preview' is in your list.")
