import streamlit as st
from google.genai import Client, types
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- 1. CONFIGURATION & SECRETS ---
st.set_page_config(page_title="SimuExpert Pro", layout="wide", page_icon="🧪")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client = Client(api_key=API_KEY)
except Exception:
    st.error("🔑 API Key missing! Add 'GEMINI_API_KEY' to Streamlit Secrets.")
    st.stop()

# --- 2. SESSION STATE FOR HISTORY ---
if "history" not in st.session_state:
    st.session_state.history = {}

if "current_project" not in st.session_state:
    st.session_state.current_project = "New Project"

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. SIDEBAR: PROJECT HISTORY ---
with st.sidebar:
    st.title("📚 Chat History")
    
    if st.button("➕ New Project", use_container_width=True):
        if st.session_state.messages:
            project_name = st.session_state.messages[0]["content"][:30] + "..."
            st.session_state.history[project_name] = st.session_state.messages
        st.session_state.messages = []
        st.session_state.current_project = "New Project"
        st.rerun()

    st.markdown("---")
    st.subheader("Previous Simulations")
    for project_name in list(st.session_state.history.keys()):
        if st.button(project_name, key=project_name, use_container_width=True):
            st.session_state.messages = st.session_state.history[project_name]
            st.session_state.current_project = project_name
            st.rerun()

# --- 4. THE ENGINEERING BRAIN ---
SYSTEM_INSTRUCTION = (
    "You are a Senior Simulation Engineer. For every query:\n"
    "1. SOLVE & EXPLAIN: Use LaTeX for equations.\n"
    "2. THE IN, PROCESS, and OUT: Break down theory, modeling, and results.\n"
    "Target: 3rd-year VIT Engineering student."
)

# --- 5. MAIN CHAT UI ---
st.title(f"🧪 {st.session_state.current_project}")

# Function to render the specific graph from your screenshot
def render_structural_graph():
    load = np.linspace(0, 7000, 100)
    yield_point = 1560
    # Deflection logic from your screenshot
    deflection = np.where(load <= yield_point, load * 0.00004, 
                          0.00004 * yield_point + (load - yield_point)**1.5 * 0.000002)
    
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(load, deflection, label='Structural Response', color='blue', linewidth=2)
    ax.axvline(x=yield_point, color='red', linestyle='--', label='Yield Limit')
    ax.set_title('Load vs. Deflection (Box Flange Analysis)')
    ax.set_xlabel('Applied Load (N)')
    ax.set_ylabel('Deflection (mm)')
    ax.grid(True, which='both', linestyle='--', alpha=0.5)
    ax.legend()
    # This is the line that shows it visually in the app
    st.pyplot(fig)

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # If the message mentions a graph was generated, we can re-render it if needed
        # but usually, we render it fresh in the chat logic below.

# --- 6. CHAT LOGIC ---
if prompt := st.chat_input("Ask a simulation question or type 'show graph'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Gemini is thinking..."):
            try:
                # 1. Generate text response
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=prompt,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
                )
                full_response = response.text
                st.markdown(full_response)
                
                # 2. Visual Logic: Handle the Graph
                if any(x in prompt.lower() for x in ["graph", "plot", "deflection", "structural"]):
                    st.write("### Visual Analysis Output")
                    render_structural_graph()
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                # Auto-update project name
                if st.session_state.current_project == "New Project":
                    new_name = prompt[:30] + "..."
                    st.session_state.current_project = new_name
                    st.session_state.history[new_name] = st.session_state.messages
                    st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")
