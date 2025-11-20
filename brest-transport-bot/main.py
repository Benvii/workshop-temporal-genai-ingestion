# Ce code est issue du tutoriel ici :
# https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps
import os

from openai import OpenAI
import streamlit as st


def make_rag_chain(model, retriever, rag_prompt = None):
    # We will use a prompt template from langchain hub.
    if not rag_prompt:
        rag_prompt = hub.pull("rlm/rag-prompt")

    # And we will use the LangChain RunnablePassthrough to add some custom processing into our chain.
    rag_chain = (
            {
                "context": RunnableLambda(get_question) | retriever | format_docs,
                "question": RunnablePassthrough()
            }
            | rag_prompt
            | model
    )

    return rag_chain

def main():
    st.title("Chatbot actu transport Brest Métropole")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = os.getenv("OPENAI_MODEL", default="gpt-3.5-turbo")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Hello, tu peux me demander l'actu sur les transport Brestois."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
