# Ce code est issue du tutoriel ici :
# https://docs.streamlit.io/develop/tutorials/chat-and-llm-apps/build-conversational-apps
import os
import logging
import requests

from openai import OpenAI
import streamlit as st

from sqlalchemy import create_engine, text
from bs4 import BeautifulSoup

from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document


def create_embedding() -> OpenAIEmbeddings:
    embedding_openai_model = os.getenv("EMBEDDING_OPENAI_MODEL", "text-embedding-3-small")

    logging.debug("Creating OpenAI embedding using model : %s", embedding_openai_model)
    return OpenAIEmbeddings(model=embedding_openai_model)

def create_vector_store(embedding: OpenAIEmbeddings) -> PGVector:
    vector_db_connexion_string = os.getenv("VECTORDB_PGDATABASE_URI", "postgresql+psycopg://postgres:ChangeMe@localhost:5432/postgres")
    vector_db_collection = os.getenv("VECTORDB_PGCOLLECTION", "brest_transport")
    logging.debug("Creating vector store with connexion string: %s", vector_db_connexion_string)

    return PGVector(
        connection=vector_db_connexion_string,
        collection_name=vector_db_collection,
        embeddings=embedding,
    )

def create_retriever(vector_store: PGVector):
    # k=4 docs récupérés, à adapter
    return vector_store.as_retriever(search_kwargs={"k": 4})

def create_rag_prompt():
    return ChatPromptTemplate.from_template(
        """
    Tu es AvelBot l'assistant des actu de transport de Brest Métropole.
    Tu es un assistant qui réponds en français en t'appuyant UNIQUEMENT sur le contexte fourni.

    CONTRAINTE :
    - Si l'information n'est pas dans le contexte, dis explicitement que tu ne sais pas.
    - Réponds de manière claire et concise.

    Contexte :
    {context}

    Question :
    {question}
    """
    )

def format_docs(docs):
    # pour le prompt : concaténation simple des contenus
    return "\n\n".join(d.page_content for d in docs)

def fetch_url_content(url: str) -> tuple[str, str]:
    """
    Récupère le titre et le texte principal d'une page web à partir de son URL.
    - Titre : contenu de la balise <title> si présente.
    - Contenu : texte de la balise <article> (si trouvée), sinon fallback sur tout le body.
    On enlève les scripts/styles et on nettoie les lignes vides.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la récupération de l'URL : {e}") from e

    soup = BeautifulSoup(response.text, "html.parser")

    # Récupération du titre de la page
    title_tag = soup.find("title")
    page_title = title_tag.get_text(strip=True) if title_tag else ""

    # Tenter de cibler l'article principal
    article = soup.find("article", class_="Node NodeNews") or soup.find("article")
    if article is not None:
        target = article
    else:
        # Fallback : tout le document
        target = soup

    # Supprimer les éléments non textuels à l'intérieur de la zone ciblée
    for tag in target(["script", "style", "noscript"]):
        tag.decompose()

    text = target.get_text(separator="\n")
    # Nettoyer les lignes vides / espaces
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned_text = "\n".join(lines)

    return page_title, cleaned_text

def make_rag_chain(model: ChatOpenAI, retriever, rag_prompt: ChatPromptTemplate = None):
    if rag_prompt is None:
        rag_prompt = create_rag_prompt()

    # On prépare un “fan-out” parallèle :
    # - context: résultat du retriever formaté pour le prompt
    # - question: la question brute
    # - source_documents: les docs bruts du retriever (pour les afficher ensuite)
    rag_inputs = RunnableParallel(
        context=retriever | format_docs,
        question=RunnablePassthrough(),
        source_documents=retriever,  # on garde la liste de docs intacts
    )

    # Chaîne principale : question (str) → dict → prompt → LLM → texte de réponse
    answer_chain = (
        rag_prompt
        | model
        | (lambda msg: msg.content)
    )

    # On assemble : on renvoie un dict answer + sources
    rag_chain = (
        rag_inputs
        | (lambda x: {
            "answer": answer_chain.invoke({"context": x["context"], "question": x["question"]}),
            "source_documents": x["source_documents"],
        })
    )

    return rag_chain

def get_total_docs() -> int:
    """
    Retourne le nombre total de documents indexés dans la collection PGVector.
    Hypothèse : schéma par défaut de langchain-postgres (langchain_pg_embedding / langchain_pg_collection).
    """
    vector_db_connexion_string = os.getenv(
        "VECTORDB_PGDATABASE_URI",
        "postgresql+psycopg://postgres:ChangeMe@localhost:5432/postgres",
    )
    vector_db_collection = os.getenv("VECTORDB_PGCOLLECTION", "brest_transport")

    engine = create_engine(vector_db_connexion_string)
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM langchain_pg_embedding e
                JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                WHERE c.name = :name
                """
            ),
            {"name": vector_db_collection},
        )
        return int(result.scalar_one())


def render_search_page(vector_store: PGVector):
    st.header("🔎 Recherche dans la base vectorielle")

    query = st.text_input("Texte de recherche", value="", placeholder="Tape ta requête ici…")
    k = st.number_input(
        "Nombre de résultats à afficher",
        min_value=1,
        max_value=100,
        value=10,
        step=1,
    )

    if query.strip():
        # Recherche vectorielle
        docs = vector_store.similarity_search(query, k=int(k))
        st.write(f"{len(docs)} document(s) trouvé(s) pour cette requête.")

        if docs:
            rows = []
            for i, doc in enumerate(docs, start=1):
                rows.append(
                    {
                        "Rank": i,
                        "Extrait": (doc.page_content or "")[:200] + ("..." if len(doc.page_content or "") > 200 else ""),
                        "Metadata": str(doc.metadata or {}),
                    }
                )
            st.dataframe(rows, use_container_width=True)
    else:
        # Rien saisi → on affiche le nombre total de documents
        total_docs = get_total_docs()
        st.info(f"Nombre total de documents indexés dans la collection : **{total_docs}**")

def render_add_document_page(vector_store: PGVector):
    st.header("📂 Gestion des documents")

    url = st.text_input("URL de l'article à ajouter", placeholder="https://...")
    col1, col2 = st.columns(2)
    with col1:
        add_button = st.button("➕ Ajouter à la base", use_container_width=True)
    with col2:
        clean_button = st.button("🧹 Vider la base de documents", use_container_width=True)

    if clean_button:
        with st.spinner("Suppression de tous les documents de la collection..."):
            try:
                # Utilise directement le vector_store pour supprimer la collection courante
                vector_store.delete_collection()
                # Recalculer le nombre de documents restants pour affichage
                remaining = get_total_docs()
            except Exception as e:
                st.error(f"Erreur lors du nettoyage de la base : {e}")
                return
        st.success(f"✅ Base vectorielle nettoyée. Il reste {remaining} document(s) dans la collection.")

    if add_button:
        url = (url or "").strip()
        if not url:
            st.error("Merci de saisir une URL valide.")
            return

        with st.spinner("Récupération et indexation de l'article..."):
            try:
                title, content = fetch_url_content(url)
                if not content or len(content) < 50:
                    st.warning("Le contenu récupéré semble vide ou trop court. Rien n'a été ajouté.")
                    return

                metadata = {
                    "source": url,
                    "type": "web_article",
                }
                if title:
                    metadata["title"] = title

                doc = Document(
                    page_content=content,
                    metadata=metadata,
                )
                vector_store.add_documents([doc])
            except Exception as e:
                st.error(f"Erreur lors de l'ajout du document : {e}")
                return

        st.success("✅ Article ajouté avec succès à la base vectorielle.")
        with st.expander("Aperçu du contenu récupéré"):
            st.text(content[:2000])

def render_chat_page(rag_chain):
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
            # Appel RAG
            result = rag_chain.invoke(prompt)
            answer = result["answer"]
            source_docs = result["source_documents"]

            st.markdown(answer)

            with st.expander("📚 Sources utilisées"):
                for i, doc in enumerate(source_docs, start=1):
                    st.markdown(f"**Source {i}**")
                    st.write((doc.page_content or "")[:500] + "...")
                    st.json(doc.metadata or {})

        st.session_state.messages.append({"role": "assistant", "content": answer})

def main():
    st.title("AvelBot, actu transport Brest Métropole")

    # Navigation entre pages
    page = st.sidebar.radio(
        "Navigation",
        ["💬 Chatbot AvelBot", "🔎 Recherche docs", "📂 Gestion des documents"],
    )

    # Création LLM LangChain
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=openai_model)

    # Embeddings + vector store + retriever + rag_chain
    embedding = create_embedding()
    vector_store = create_vector_store(embedding)
    retriever = create_retriever(vector_store)
    rag_prompt = create_rag_prompt()
    rag_chain = make_rag_chain(llm, retriever, rag_prompt)

    if page == "💬 Chatbot AvelBot":
        render_chat_page(rag_chain)
    elif page == "🔎 Recherche docs":
        render_search_page(vector_store)
    else:
        render_add_document_page(vector_store)

if __name__ == "__main__":
    main()
