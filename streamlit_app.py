import os

from dotenv import load_dotenv

load_dotenv()

import streamlit as st
from app import main_llm_call

if "google_api_key" not in st.session_state:
    st.session_state.google_api_key = None
    if os.getenv("GOOGLE_API_KEY"):
        print("Google API key found in the environment variables.")
        st.session_state.google_api_key = os.getenv("GOOGLE_API_KEY")

if "chat_disabled" not in st.session_state:
    print("Initializing chat_disabled as False")
    st.session_state.chat_disabled = "False"


# If the API key has not been submitted yet
if st.session_state.google_api_key is None:
    st.title("AI news interpreter")  # Title for the key entry screen
    st.subheader("Enter your Google Generative AI API Key")

    # Text input for the API key with password type
    api_key_input = st.text_input("API Key:", type="password", key="api_key_input")

    # Button to submit the key
    if st.button("Submit Key"):
        if api_key_input:
            # Store the key in session state
            st.session_state.google_api_key = api_key_input
            # Rerun the app to trigger the transition to the chat UI
            st.rerun()
        else:
            # Show a warning if the input is empty
            st.warning("Please enter your API key.")
else:
    # --- Main Chat Application UI ---
    st.title("AI news interpreter")  # Title for the chat screen

    # Initial success message displayed above the chat
    st.write(
        """
        This agent is ready to assist you with the article. How can I be of help?
        Type 'quit' to quit the app.
        """
    )

    # Initialize chat history in session state if it doesn't exist
    # This check is inside the 'else' block, so history is cleared if user
    # refreshes or the app reruns without the key in state (e.g., first load)
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # This runs only once after the key is entered and history is initialized
    if len(st.session_state.messages) == 0:
        initial_ai_message = (
            "Which article shall I help you with today? Please drop the URL below."
        )
        st.session_state.messages.append(
            {"role": "assistant", "content": initial_ai_message}
        )
        # Display the initial message immediately
        with st.chat_message("assistant"):
            st.write(initial_ai_message)

    if st.session_state.chat_disabled == "False":
        # Add a text input box for the user to enter their message
        prompt = st.chat_input(
            "Enter URL in quotes and ask a question about the article."
        )

        # Process user input if something was typed and submitted
        if prompt:
            # Add user message to chat history
            st.session_state.messages.append(
                {"role": "user", "content": prompt.strip()}
            )
            # Display user message immediately
            with st.chat_message("user"):
                st.write(prompt)

            # Handling 'quit' command
            if prompt.lower() == "quit":
                print("User wants to quit the app. Disabling chat.")
                response = "Okay, goodbye! Feel free to rerun the app whenever you need assistance."
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
                # Display the assistant's goodbye message
                with st.chat_message("assistant"):
                    st.write(response)
                st.session_state.chat_disabled = "True"
                st.rerun()

            else:
                # Call the placeholder AI function, passing the stored API key
                # You will replace this with your actual AI call using the key
                prompt = prompt.strip()
                ai_response, tool_output = main_llm_call(
                    st.session_state.messages[:-1],
                    st.session_state.messages[-1],
                    st.session_state.google_api_key,
                )

                if tool_output:
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": f"TOOL USED! TOOL OUTPUT => {tool_output}",
                        }
                    )
                    # Display the tool's response
                    with st.chat_message("assistant"):
                        st.write(f"TOOL USED! TOOL OUTPUT => {tool_output}")

                # Adding assistant response to chat history
                st.session_state.messages.append(
                    {"role": "assistant", "content": ai_response}
                )
                # Display the assistant's response
                with st.chat_message("assistant"):
                    st.write(ai_response)
    else:
        # If the chat is disabled, show a message
        st.warning("Chat is currently disabled. Please re-enable it to start again.")
        # Add buttons to re-enable the chat
        but1 = st.button("Re-enable Chat with old history")
        but2 = st.button("Re-enable Chat with new history")

        # Check which button was pressed and re-enable chat accordingly
        if but1:
            print(
                "User wants to Re-enable the chat with the old history. Enabling chat."
            )
            st.session_state.chat_disabled = "False"
            st.rerun()
        elif but2:
            print(
                "User wants to Re-enable a fresh chat. Enabling chat with new history."
            )
            st.session_state.chat_disabled = "False"
            st.session_state.messages = []
            st.rerun()
