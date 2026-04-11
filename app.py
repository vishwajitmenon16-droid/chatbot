import streamlit as st
from google.genai import Client, types
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

# --- 1. CONFIGURATION & SECRETS ---
st.set_page_config(page_title="SimuExpert Pro v4.0", layout="wide", page_icon="⚡")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client = Client(api_key=API_KEY)
except Exception:
    st.error("🔑 API Key missing! Add 'GEMINI_API_KEY' to Streamlit Secrets.")
    st.stop()

# --- 2. SESSION STATE (History & Data) ---
if "history" not in st.session_state:
    st.session_state.history = {}
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_project" not in st.session_state:
    st.session_state.current_project = "New Simulation"

# --- 3. SIDEBAR: CONTROLS & HISTORY ---
with st.sidebar:
    st.title("🎮 Control Room")
    
    # Feature 1: Dynamic Sliders (The "Digital Twin" Idea)
    st.subheader("Physical Parameters")
    temp = st.slider("Ambient Temp (°C)", -10, 100, 25)
    load_factor = st.slider("Load Factor (%)", 0, 150, 100)
    
    # Feature 2: File Upload (The "Data Analyst" Idea)
    st.subheader("Simulation Data")
    uploaded_file = st.file_uploader("Upload Simulink CSV/Excel", type=["csv", "xlsx"])
    
    st.markdown("---")
    st.subheader("📚 Project History")
    if st.button("➕ New Project", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_project = "New Simulation"
        st.rerun()

    for name in list(st.session_state.history.keys()):
        if st.button(name, key=name, use_container_width=True):
            st.session_state.messages = st.session_state.history[name]
            st.session_state.current_project = name
            st.rerun()

# --- 4. SYSTEM INSTRUCTION ---
SYSTEM_INSTRUCTION = (
    "You are a Senior Simulation Engineer. For every query:\n"
    "1. SOLVE & EXPLAIN: Use LaTeX for equations.\n"
    "2. THE IN, PROCESS, and OUT: Break down theory, modeling, and results.\n"
    f"Current Simulation Context: Temp={temp}°C, Load={load_factor}%.\n"
    "Target: 3rd-year VIT Engineering student."
)

# --- 5. MAIN INTERFACE ---
st.title(f"⚡ {st.session_state.current_project}")

# Handle Uploaded Data Visually
if uploaded_file:
    st.success("Data File Loaded!")
    df_uploaded = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    with st.expander("View Raw Data"):
        st.dataframe(df_uploaded.head())
    st.line_chart(df_uploaded.select_dtypes(include=[np.number]))

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. CHAT & VISUALIZATION LOGIC ---
if prompt := st.chat_input("Ask a question (e.g., 'Analyze the structural response with current parameters')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Gemini 3 is simulating..."):
            try:
                # Add context about uploaded file if it exists
                context_prompt = prompt
                if uploaded_file:
                    context_prompt += f"\n\nNote: The user has uploaded a data file with columns: {list(df_uploaded.columns)}"

                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=context_prompt,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
                )
                
                full_response = response.text
                st.markdown(full_response)
                
                # Custom Visualization for "Structural/Deflection" prompts
                if any(x in prompt.lower() for x in ["structural", "deflection", "plot", "graph"]):
                    fig, ax = plt.subplots(figsize=(8, 4))
                    x_vals = np.linspace(0, 10, 100)
                    # Use the slider 'load_factor' to change the graph dynamically
                    y_vals = (x_vals**2) * (load_factor/100) 
                    ax.plot(x_vals, y_vals, label=f"Response at {load_factor}% Load")
                    ax.set_title("Dynamic Structural Response")
                    ax.legend()
                    st.pyplot(fig)

                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                # Update Project Name in History
                if st.session_state.current_project == "New Simulation":
                    new_name = prompt[:25] + "..."
                    st.session_state.current_project = new_name
                    st.session_state.history[new_name] = st.session_state.messages
                    st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")
