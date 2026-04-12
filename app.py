import streamlit as st
from google.genai import Client, types
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SimuExpert Solver Pro", layout="wide", page_icon="⚙️")

# PREMIUM DARK THEME CSS
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    section[data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 1px solid #30363d; }
    [data-testid="stChatMessage"] {
        background-color: #1f2937 !important; 
        border: 1px solid #374151 !important;
        border-radius: 12px !important;
        padding: 15px !important;
        margin-bottom: 15px !important;
    }
    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li, [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] h1, [data-testid="stChatMessage"] h2, [data-testid="stChatMessage"] h3,
    [data-testid="stMarkdownContainer"], .katex {
        color: #e5e7eb !important; 
    }
    h1, h2, h3, label { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client = Client(api_key=API_KEY)
except Exception:
    st.error("🔑 API Key missing! Check Streamlit Secrets.")
    st.stop()

# --- 2. PHYSICS ENGINES ---
def solve_thermal(initial_temp, ambient_temp):
    t = np.linspace(0, 3600, 100)
    def model(T, t):
        k, Q_gen = 0.001, 0.05
        return k * (ambient_temp - T) + Q_gen
    T = odeint(model, initial_temp, t)
    return t, T

def solve_structural(load_val):
    x = np.linspace(0, 1, 100)
    deflection = (load_val * x**2 / 5000) * (3 - x)
    return x, deflection

# --- 3. SESSION STATE ---
if "history" not in st.session_state:
    st.session_state.history = {} 
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_project" not in st.session_state:
    st.session_state.current_project = "New Simulation"

# --- 4. SIDEBAR: TOOLS & HISTORY ---
with st.sidebar:
    st.title("📚 History")
    if st.button("➕ Start New Project", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_project = "New Simulation"
        st.rerun()
    
    st.markdown("---")
    for project_name in list(st.session_state.history.keys()):
        if st.button(project_name, use_container_width=True):
            st.session_state.messages = st.session_state.history[project_name]
            st.session_state.current_project = project_name
            st.rerun()

    st.markdown("---")
    st.header("📂 Data Analyst")
    uploaded_file = st.file_uploader("Upload Simulink CSV/Excel", type=["csv", "xlsx"])

    st.header("⚙️ Solver Settings")
    sim_mode = st.selectbox("Physics Mode", ["Thermal Analysis", "Structural Load"])
    input_mag = st.slider("Magnitude (Load/Temp)", 0, 1000, 100)

# --- 5. SYSTEM INSTRUCTION ---
SYSTEM_INSTRUCTION = (
    "You are a Senior Simulation Engineer. For every query:\n"
    "1. MATH: Provide formulas in LaTeX.\n"
    "2. DATA ANALYSIS: If a file is uploaded, analyze the trends and columns.\n"
    "3. IN/PROCESS/OUT: Breakdown theory, Simscape steps, and results.\n"
    "Target: 3rd-year VIT Engineering student."
)

# --- 6. MAIN INTERFACE ---
st.title(f"🔍 {st.session_state.current_project}")

# Data Preview if file is uploaded
if uploaded_file:
    with st.expander("📊 Preview Uploaded Data"):
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        st.dataframe(df.head())
        st.line_chart(df.select_dtypes(include=[np.number]))

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 7. CHAT & SOLVER LOGIC ---
if prompt := st.chat_input("Ask about your data or type 'Simulate'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing & Solving..."):
            try:
                # Add file context to the AI if it exists
                ai_prompt = prompt
                if uploaded_file:
                    ai_prompt += f"\n\nContext: The user has uploaded a file named {uploaded_file.name} with columns: {list(df.columns)}. Use this for your analysis."

                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=ai_prompt,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
                )
                res_text = response.text
                st.markdown(res_text)

                # Solver Graph Logic
                if any(x in prompt.lower() for x in ["simulate", "solve", "graph", "plot"]):
                    st.divider()
                    plt.style.use('dark_background')
                    fig, ax = plt.subplots(figsize=(8, 4))
                    fig.patch.set_facecolor('#1f2937')
                    ax.set_facecolor('#1f2937')
                    
                    if sim_mode == "Thermal Analysis":
                        t, T = solve_thermal(25, input_mag)
                        ax.plot(t, T, color='#ff4b4b', linewidth=2, label='Temp Rise')
                        ax.set_xlabel("Time (s)"); ax.set_ylabel("Temp (°C)")
                    else:
                        x, y = solve_structural(input_mag)
                        ax.plot(x, -y, color='#00d1ff', linewidth=2, label='Deflection')
                        ax.set_xlabel("Position (m)"); ax.set_ylabel("Deflection (mm)")
                    
                    ax.grid(True, alpha=0.2); ax.legend()
                    st.pyplot(fig)

                st.session_state.messages.append({"role": "assistant", "content": res_text})
                
                if st.session_state.current_project == "New Simulation":
                    st.session_state.current_project = prompt[:25] + "..."
                
                st.session_state.history[st.session_state.current_project] = st.session_state.messages
                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")
