import streamlit as st
from google.genai import Client, types
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="SimuExpert Solver Pro", layout="wide", page_icon="⚙️")

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client = Client(api_key=API_KEY)
except Exception:
    st.error("🔑 API Key missing! Add 'GEMINI_API_KEY' to Streamlit Secrets.")
    st.stop()

# --- 2. THE NUMERICAL SOLVERS (The "Ansys/Simulink" Engine) ---
def solve_thermal_runaway(initial_temp, ambient_temp, time_horizon=3600):
    """Solves the 1st order thermal differential equation: dT/dt = k(Tamb - T) + Q_gen"""
    def model(T, t):
        k = 0.001  # Thermal coupling coefficient
        Q_gen = 0.05 # Internal heat generation (Simplified)
        dTdt = k * (ambient_temp - T) + Q_gen
        return dTdt
    
    t = np.linspace(0, time_horizon, 100)
    T = odeint(model, initial_temp, t)
    return t, T

def solve_structural_deflection(load):
    """Solves for beam deflection (Simplified Euler-Bernoulli logic)"""
    x = np.linspace(0, 1, 100)
    # y = (F*x^2 / 6EI) * (3L - x)
    deflection = (load * x**2 / 5000) * (3 - x) 
    return x, deflection

# --- 3. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = {}

# --- 4. SIDEBAR & CONTROLS ---
with st.sidebar:
    st.header("🎛️ Solver Parameters")
    sim_type = st.selectbox("Simulation Mode", ["Thermal Analysis", "Structural Load", "General Engineering"])
    input_val = st.slider("Input Magnitude (Load/Temp)", 0, 500, 100)
    
    if st.button("➕ New Project"):
        st.session_state.messages = []
        st.rerun()

# --- 5. SYSTEM INSTRUCTION ---
SYSTEM_INSTRUCTION = (
    "You are a Senior Simulation Engineer. For every prompt:\n"
    "1. MATHEMATICAL DERIVATION: Provide the differential equations used.\n"
    "2. THE IN, PROCESS, OUT: Explain why the numerical solver produced this specific result.\n"
    "3. SIMULINK COMPARISON: Explain how this result matches a Simscape 'Thermal Liquid' or 'Multibody' block."
)

# --- 6. MAIN CHAT & SOLVER LOGIC ---
st.title(f"⚙️ Engineering Solver: {sim_type}")

# Display History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask to 'Simulate' the current system..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Running Numerical Integration..."):
            try:
                # API Reasoning
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=f"User wants to {prompt} using {sim_type} at magnitude {input_val}.",
                    config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
                )
                st.markdown(response.text)
                
                # --- ACTUAL SOLVER EXECUTION ---
                st.divider()
                st.subheader("📊 Solver Output (Visualized)")
                fig, ax = plt.subplots(figsize=(8, 4))

                if sim_type == "Thermal Analysis":
                    t, T = solve_thermal_runaway(25, input_val)
                    ax.plot(t, T, 'r-', label='Temperature Rise')
                    ax.set_ylabel("Temp (°C)")
                    ax.set_xlabel("Time (s)")
                
                elif sim_type == "Structural Load":
                    x, y = solve_structural_deflection(input_val)
                    ax.plot(x, -y, 'b-', label='Beam Deflection')
                    ax.set_ylabel("Deflection (mm)")
                    ax.set_xlabel("Position (m)")
                
                ax.grid(True, alpha=0.3)
                ax.legend()
                st.pyplot(fig)

                st.session_state.messages.append({"role": "assistant", "content": response.text})

            except Exception as e:
                st.error(f"Solver Error: {e}")
