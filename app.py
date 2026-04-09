import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np

# --- 1. SECURE CONFIGURATION ---
st.set_page_config(page_title="SimuExpert AI", layout="wide", page_icon="⚡")

# Try to fetch the key from Streamlit Cloud Secrets
try:
    # Ensure this matches the key name in your Streamlit Settings > Secrets
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except Exception:
    st.error("🔑 **API Key Missing!** Go to Streamlit Settings > Secrets and add: GEMINI_API_KEY = 'your_key'")
    st.stop()

# --- 2. THE "IN AND OUT" REASONING ENGINE ---
# This system prompt forces the AI to provide the explanation depth you need
SYSTEM_INSTRUCTION = (
    "You are an expert Simulation Engineer. For every user query:\n"
    "1. THE IN (Theory): Explain the physics and engineering principles involved.\n"
    "2. THE PROCESS (Modeling): Explain how to set this up in Simulink, Simscape, or Ansys.\n"
    "3. THE OUT (Application): Explain how the simulation results impact real-world design.\n"
    "Target Audience: 3rd-year Engineering Student at VIT Chennai."
)

# Initialize the model with the instruction
# We use 'gemini-1.5-flash' for speed and reliability
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=SYSTEM_INSTRUCTION
)

# --- 3. PERSISTENT CHAT HISTORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 4. USER INTERFACE ---
st.title("🤖 SimuExpert: AI Simulation Project")
st.markdown("---")

# Sidebar for controls
with st.sidebar:
    st.header("Control Panel")
    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()
    st.info("This bot explains the engineering 'In and Out' of your simulation prompts.")

# Display existing messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 5. CHAT LOGIC ---
if prompt := st.chat_input("Ex: Explain the simulation of a 3-phase inverter for EVs"):
    # Save and display user prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Processing Engineering Model..."):
            try:
                # Use a chat session to maintain context of the conversation
                chat = model.start_chat(history=[])
                response = chat.send_message(prompt)
                
                # Output the explanation
                full_response = response.text
                st.markdown(full_response)
                
                # Visual Logic: If user asks for a simulation, show a dummy data trend
                if any(word in prompt.lower() for word in ["simulate", "graph", "plot", "test"]):
                    st.divider()
                    st.write("### Predicted Simulation Trend")
                    data = pd.DataFrame({
                        'Time (s)': np.linspace(0, 10, 100),
                        'Output Value': np.sin(np.linspace(0, 10, 100)) + np.random.normal(0, 0.1, 100)
                    })
                    st.line_chart(data, x='Time (s)', y='Output Value')

                # Save assistant response
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                st.error(f"Error: {e}")
                st.info("If you see 'NotFound', ensure your API key is correct and your internet connection is stable.")
