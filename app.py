import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np

# --- 1. CONFIGURATION & SECURITY ---
# Access your API key from Streamlit Secrets (for GitHub hosting)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("Please set the GEMINI_API_KEY in your Streamlit Secrets or secrets.toml.")
    st.stop()

st.set_page_config(page_title="SimuExpert AI", layout="wide")

# --- 2. SYSTEM INSTRUCTIONS (The "Brain") ---
SYSTEM_PROMPT = """
You are an expert AI Simulation Engineer specializing in Electric Vehicles and Control Systems.
For every user prompt, follow this structure:
1. THE CONCEPT (In): Explain the fundamental physics or engineering theory.
2. THE MODEL: Describe how this would be simulated in tools like Simulink, Simscape, or Ansys.
3. THE OUTCOME (Out): Explain what the results mean for real-world EV performance.
Use technical terms like 'Torque Ripple', 'State of Charge (SOC)', or 'Proportional-Integral (PI) Control' accurately.
"""

model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)

# --- 3. UI LAYOUT ---
st.title("⚡ SimuExpert: Advanced Engineering Chatbot")
st.markdown("---")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for Simulation Parameters
with st.sidebar:
    st.header("Simulation Workbench")
    motor_rpm = st.slider("Motor RPM", 0, 15000, 5000)
    battery_temp = st.slider("Battery Temp (°C)", -10, 60, 25)
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. CHAT LOGIC ---
if prompt := st.chat_input("Ask about motor efficiency, battery thermal modeling, etc."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI Response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing Physics..."):
            # Include chat history for context-aware explanations
            chat = model.start_chat(history=[
                {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
                for m in st.session_state.messages[:-1]
            ])
            
            response = chat.send_message(prompt)
            full_response = response.text
            st.markdown(full_response)
            
            # Context-Aware Visualization
            if "efficiency" in prompt.lower() or "power" in prompt.lower():
                data = pd.DataFrame(np.random.randn(20, 2), columns=['Efficiency', 'Power Loss'])
                st.line_chart(data)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
