from dotenv import load_dotenv
import os
import streamlit as st
import google.genai as genai
from google.genai import types
import datetime
import uuid

# load .env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
CUSTOM_INSTRUCTIONS = os.getenv("CUSTOM_INSTRUCTIONS")

# initialize gemini client
genai_client = genai.Client(api_key=GOOGLE_API_KEY)
search_tool = types.Tool(google_search=types.GoogleSearch())
chat = genai_client.chats.create(
    model=GEMINI_MODEL,
    history=[],
    config=types.GenerateContentConfig(
        system_instruction=CUSTOM_INSTRUCTIONS,
        tools=[search_tool],
    ),
)

if "chat" not in st.session_state:
    st.session_state.chat = str(uuid.uuid4())

if "pending" not in st.session_state:
    st.session_state.pending = False

if "history" not in st.session_state:
    st.session_state.history = {}

chat_id = st.session_state.chat

if chat_id not in st.session_state.history:
    # initialize history
    st.session_state.history[chat_id] = []

# sidebar
with st.sidebar:
    st.title("AIdent")
    st.markdown(f"**Model:** {GEMINI_MODEL}")

    if st.button("New chat", use_container_width=True):
        chat_id = str(uuid.uuid4())
        st.session_state.chat = chat_id
        st.session_state.history[chat_id] = []
        st.session_state.pending = False
        st.rerun()

    chat_list = list(st.session_state.history.keys())
    selected_chat_id = st.selectbox("Select chat", chat_list, index=chat_list.index(st.session_state.chat))
    if selected_chat_id != st.session_state.chat:
        st.session_state.chat = selected_chat_id
        st.session_state.pending = False
        st.rerun()

# chat interface
for message in st.session_state.history[chat_id]:
    with st.chat_message(message["role"]):
        st.markdown(f"{message['content']}\n\n<span style='font-size:10px;color:gray;'>{message['time']}</span>", unsafe_allow_html=True)

prompt = st.chat_input("Ask a question")

if prompt and not st.session_state.pending:
    now = datetime.datetime.now().strftime("%H:%M")
    st.session_state.history[chat_id].append({"role": "user", "content": prompt, "time": now})
    st.session_state.history[chat_id].append({"role": "assistant", "content": "Thinking...", "time": now})
    st.session_state.pending = True
    st.rerun()

if st.session_state.pending:
    try:
        user_message = st.session_state.history[chat_id][-2]["content"]
        response = chat.send_message(message=user_message)
        now = datetime.datetime.now().strftime("%H:%M")
        st.session_state.history[chat_id][-1] = {"role": "assistant", "content": response.text, "time": now}
    except Exception as e:
        now = datetime.datetime.now().strftime("%H:%M")
        st.session_state.history[chat_id][-1] = {"role": "assistant", "content": f"Error: {e}", "time": now}
    st.session_state.pending = False
    st.rerun()