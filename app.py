import streamlit as st
import random
import time

# --- APP CONFIG ---
st.set_page_config(page_title="SimuBot: AI Simulation Assistant", layout="centered")
st.title("🤖 SimuBot: AI Project Assistant")
st.subheader("Simulating EV Performance & Control Systems")

# --- SIMULATION ENGINE (The 'AI' Logic) ---
def run_simulation(parameter_x):
    """Simple simulation logic: Replace this with your actual AI/Math model"""
    time.sleep(1) # Simulate processing
    result = parameter_x * random.uniform(0.8, 1.2)
    return result

# --- CHATBOT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask about your simulation (e.g., 'Predict EV motor efficiency at 5000 RPM')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Bot Response Logic
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        # Simple Logic: If user mentions 'simulate', run the function
        if "simulate" in prompt.lower():
            val = run_simulation(100)
            full_response = f"I've run the simulation. Based on your inputs, the predicted efficiency is {val:.2f}%."
        else:
            full_response = "I am ready to help with your simulation. Try saying 'Simulate motor heat'."
        
        response_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
