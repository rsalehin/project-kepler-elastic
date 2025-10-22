import streamlit as st

# --- Page Configuration ---
# Set the page title and icon
st.set_page_config(
    page_title="Kepler AI",
    page_icon="🔭"
)

# --- Title ---
st.title("Kepler AI Chat 🔭✨")
st.caption("Your AI Research Assistant for Exoplanets and Astronomy")

# --- Initialize Chat History ---
# Streamlit's session_state acts like a memory for each user's session
if "messages" not in st.session_state:
    st.session_state.messages = []
    print("Initialized chat history.")

# --- Display Chat Messages ---
# Loop through the stored messages and display them
for message in st.session_state.messages:
    with st.chat_message(message["role"]): # "user" or "assistant"
        st.markdown(message["content"])

# --- Chat Input Box ---
# This command displays the input box at the bottom
if prompt := st.chat_input("Ask Kepler about exoplanets..."):
    
    # 1. Display the user's message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 2. Add the user's message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # --- This is where we will call our AI agent later ---
    # For now, just add a dummy "assistant" response
    
    response = f"Kepler AI received: **{prompt}** (Next step is to connect this to our Gemini agent!)"
    
    # 3. Display the dummy assistant response
    with st.chat_message("assistant"):
        st.markdown(response)
        
    # 4. Add the assistant's response to history
    st.session_state.messages.append({"role": "assistant", "content": response})
