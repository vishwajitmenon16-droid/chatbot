import streamlit as st
from google.genai import Client, types
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SimuExpert Solver Pro", layout="wide", page_icon="⚙️")

# FIXED: Changed unsafe_allow_value to unsafe_allow_html
st.markdown("""
    <style>
    .stChatMessage { background-color: #f0f2f6; border-radius: 10px; padding: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

try:
    # Ensure 'GEMINI_API_KEY' is set in your Streamlit Cloud Secrets
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client = Client(api_key=API_KEY)
except Exception:
    st.error("🔑 API Key missing! Add 'GEMINI_API_KEY' to Streamlit Secrets.")
    st.stop()

# --- 2. PHYSICS ENGINES (The Solver Module) ---
def solve_thermal(initial_temp, ambient_temp):
    t = np.linspace(0, 3600, 100)
    def model(T, t):
        k, Q_gen = 0.001, 0.05
        return k * (ambient_temp - T) + Q_gen
    T = odeint(model, initial_temp, t)
    return t, T

def solve_structural(load_val):
    x = np.linspace(0, 1, 100)
    # Euler-Bernoulli Beam Deflection approximation
    deflection = (load_val * x**2 / 5000) * (3 - x)
    return x, deflection

# --- 3. SESSION STATE (History Management) ---
if "history" not in st.session_state:
    st.session_state.history = {} 
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_project" not in st.session_state:
    st.session_state.current_project = "New Simulation"

# --- 4. SIDEBAR: PROJECT HISTORY & PARAMETERS ---
with st.sidebar:
    st.title("📚 Simulation History")
    
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
    st.header("⚙️ Solver Settings")
    sim_mode = st.selectbox("Physics Mode", ["Thermal Analysis", "Structural Load"])
    input_mag = st.slider("Magnitude (Load/Temp)", 0, 1000, 100)
    st.info("Uses Scipy ODEint for real-world physical responses.")

# --- 5. SYSTEM INSTRUCTION ---
SYSTEM_INSTRUCTION = (
    "You are a Senior Simulation Engineer. For every query:\n"
    "1. MATH: Provide the differential equations or formulas in LaTeX.\n"
    "2. IN/PROCESS/OUT: Breakdown the theory, Simscape steps, and real-world result.\n"
    "Target: 3rd-year VIT Engineering student."
)

# --- 6. MAIN INTERFACE ---
st.title(f"🔍 {st.session_state.current_project}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 7. CHAT & SOLVER LOGIC ---
if prompt := st.chat_input("Ask a question or type 'Simulate'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Solving Physics..."):
            try:
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=f"Mode: {sim_mode}, Input: {input_mag}. Prompt: {prompt}",
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
                )
                res_text = response.text
                st.markdown(res_text)

                if any(x in prompt.lower() for x in ["simulate", "solve", "graph", "plot"]):
                    st.divider()
                    st.subheader("📊 Numerical Solver Output")
                    fig, ax = plt.subplots(figsize=(8, 4))
                    
                    if sim_mode == "Thermal Analysis":
                        t, T = solve_thermal(25, input_mag)
                        ax.plot(t, T, color='#e74c3c', label=f'Temp Rise (Amb={input_mag}°C)')
                        ax.set_xlabel("Time (s)"); ax.set_ylabel("Temp (°C)")
                    else:
                        x, y = solve_structural(input_mag)
                        ax.plot(x, -y, color='#3498db', label=f'Deflection (Load={input_mag}N)')
                        ax.set_xlabel("Position (m)"); ax.set_ylabel("Deflection (mm)")
                    
                    ax.grid(True, alpha=0.3); ax.legend()
                    st.pyplot(fig)

                st.session_state.messages.append({"role": "assistant", "content": res_text})
                
                if st.session_state.current_project == "New Simulation":
                    project_title = prompt[:25] + "..."
                    st.session_state.current_project = project_title
                
                st.session_state.history[st.session_state.current_project] = st.session_state.messages
                st.rerun()

            except Exception as e:
                st.error(f"Solver Error: {e}")
