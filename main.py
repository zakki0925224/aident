from dotenv import load_dotenv
import os
import streamlit as st
import google.genai as genai
from google.genai import types
import datetime
import uuid

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
CUSTOM_INSTRUCTIONS = os.getenv("CUSTOM_INSTRUCTIONS")

# check if required environment variables are set
if not GOOGLE_API_KEY or not GEMINI_MODEL or not CUSTOM_INSTRUCTIONS:
    st.error("Please set the GOOGLE_API_KEY, GEMINI_MODEL, and CUSTOM_INSTRUCTIONS environment variables.")
    st.stop()

# initialize genai client
genai_client = genai.Client(api_key=GOOGLE_API_KEY)
search_tool = types.Tool(google_search=types.GoogleSearch())

# initialize session states
if "chat" not in st.session_state:
    st.session_state.chat = str(uuid.uuid4())

if "pending" not in st.session_state:
    st.session_state.pending = False

if "history" not in st.session_state:
    st.session_state.history = {}

if "gemini_chats" not in st.session_state:
    st.session_state.gemini_chats = {}

chat_id = st.session_state.chat

if chat_id not in st.session_state.history:
    st.session_state.history[chat_id] = []

if chat_id not in st.session_state.gemini_chats:
    st.session_state.gemini_chats[chat_id] = genai_client.chats.create(
        model=GEMINI_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=CUSTOM_INSTRUCTIONS,
            tools=[search_tool],
        ),
    )

chat = st.session_state.gemini_chats[chat_id]

# sidebar
with st.sidebar:
    st.title("AIdent")
    st.markdown(f"**Model:** {GEMINI_MODEL}")

    if st.button("New chat", use_container_width=True):
        new_chat_id = str(uuid.uuid4())
        st.session_state.chat = new_chat_id
        st.session_state.history[new_chat_id] = []
        st.session_state.pending = False
        st.session_state.gemini_chats[new_chat_id] = genai_client.chats.create(
            model=GEMINI_MODEL,
            config=types.GenerateContentConfig(
                system_instruction=CUSTOM_INSTRUCTIONS,
                tools=[search_tool],
            ),
        )
        st.rerun()

    chat_list = list(st.session_state.history.keys())
    selected_chat_id = st.selectbox("Select chat", chat_list, index=chat_list.index(chat_id))
    if selected_chat_id != st.session_state.chat:
        st.session_state.chat = selected_chat_id
        st.session_state.pending = False
        st.rerun()

# main chat area
for message in st.session_state.history[chat_id]:
    with st.chat_message(message["role"]):
        st.markdown(
            f"{message['content']}\n\n"
            f"<span style='font-size:10px;color:gray;'>{message['time']}</span>",
            unsafe_allow_html=True
        )

# user input
prompt = st.chat_input("Ask a question")

# handle user input
if prompt and not st.session_state.pending:
    now = datetime.datetime.now().strftime("%H:%M")
    st.session_state.history[chat_id].append({"role": "user", "content": prompt, "time": now})
    st.session_state.history[chat_id].append({"role": "assistant", "content": "Thinking...", "time": now})
    st.session_state.pending = True
    st.rerun()

# handle response from gemini
if st.session_state.pending:
    try:
        user_message = st.session_state.history[chat_id][-2]["content"]
        response = chat.send_message(message=user_message)
        now = datetime.datetime.now().strftime("%H:%M")
        st.session_state.history[chat_id][-1] = {
            "role": "assistant",
            "content": response.text,
            "time": now
        }
    except Exception as e:
        now = datetime.datetime.now().strftime("%H:%M")
        st.session_state.history[chat_id][-1] = {
            "role": "assistant",
            "content": f"Error: {e}",
            "time": now
        }
    st.session_state.pending = False
    st.rerun()
