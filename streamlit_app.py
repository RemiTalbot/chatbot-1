import streamlit as st
import requests
from openai import OpenAI
import time

WEBHOOK_URL = "https://hook.eu2.make.com/266bbw6u3mopx4g9jqizm9glnivc6dmu"
ASSISTANT_ID = "asst_5c4B9QMgs3gugmzkt4VdpKRJ"

# Récupérer la clé API depuis les secrets de Streamlit
openai_api_key = st.secrets["openai"]["api_key"]

st.title("💬 Audit IA par Made in AI")
st.write("Découvrez les applications potentielles de l'IA dans votre quotidien professionnel.")

st.info("""
Cette application vous permet de discuter avec un assistant IA de votre quotidien professionnel. 
L'objectif est de collecter des informations sur vos tâches et défis quotidiens afin que les équipes de Made in AI 
puissent analyser les résultats et identifier les applications potentielles de l'IA pour améliorer votre travail.

Vos échanges seront analysés par nos consultants pour proposer des solutions IA adaptées à vos besoins.
""")

user_name = st.text_input("Entrez votre nom :")
user_email = st.text_input("Entrez votre email pour continuer :")
user_company = st.text_input("Entrez le nom de votre entreprise :")

if user_name and user_email and user_company:
    st.write(f"Bienvenue, {user_name} ({user_email}) de {user_company} !")
    
    if "info_sent" not in st.session_state:
        data = {
            "type": "user_info",
            "name": user_name,
            "email": user_email,
            "company": user_company,
        }
        try:
            response = requests.post(WEBHOOK_URL, json=data)
            if response.status_code == 200:
                st.success("Vos informations ont été enregistrées avec succès.")
            else:
                st.error(f"Échec de l'enregistrement des informations. Statut: {response.status_code}")
        except Exception as e:
            st.error(f"Erreur lors de l'enregistrement des informations : {e}")
        st.session_state.info_sent = True

    client = OpenAI(api_key=openai_api_key)

    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    if "messages" not in st.session_state:
        st.session_state.messages = []
        
        # Message initial de l'IA
        initial_message = (
            "Bonjour ! Je suis l'assistant IA de Made in AI. Je suis ici pour discuter de votre quotidien professionnel "
            "et comprendre comment l'IA pourrait potentiellement améliorer vos processus de travail. "
            "Pourriez-vous me décrire une journée typique dans votre travail ? "
            "Quelles sont vos principales tâches et les défis que vous rencontrez régulièrement ?"
        )
        st.session_state.messages.append({"role": "assistant", "content": initial_message})

    if "sent_messages" not in st.session_state:
        st.session_state.sent_messages = set()

    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                send_key = f"send_{idx}"
                if send_key not in st.session_state.sent_messages:
                    if st.button("📤 Envoyer cette information au consultant IA", key=send_key):
                        send_data = {
                            "type": "send_to_consultant",
                            "name": user_name,
                            "email": user_email,
                            "company": user_company,
                            "message_index": idx,
                            "message_role": message["role"],
                            "message_content": message["content"],
                        }
                        try:
                            response = requests.post(WEBHOOK_URL, json=send_data)
                            if response.status_code == 200:
                                st.success("L'information a été envoyée avec succès au consultant IA.")
                                st.session_state.sent_messages.add(send_key)
                            else:
                                st.error(f"Échec de l'envoi de l'information. Statut: {response.status_code}")
                        except Exception as e:
                            st.error(f"Erreur lors de l'envoi de l'information : {e}")
                else:
                    st.write("✅ Information envoyée au consultant IA")

    if prompt := st.chat_input("Décrivez votre journée de travail, vos tâches ou vos défis..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
        )

        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=ASSISTANT_ID
        )

        with st.spinner("L'assistant analyse votre réponse..."):
            while run.status != "completed":
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )

        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )

        assistant_message = messages.data[0].content[0].text.value

        with st.chat_message("assistant"):
            st.markdown(assistant_message)
        
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
        
        send_key = f"send_{len(st.session_state.messages)-1}"
        if send_key not in st.session_state.sent_messages:
            if st.button("📤 Envoyer cette information au consultant IA", key=send_key):
                send_data = {
                    "type": "send_to_consultant",
                    "name": user_name,
                    "email": user_email,
                    "company": user_company,
                    "message_index": len(st.session_state.messages)-1,
                    "message_role": "assistant",
                    "message_content": assistant_message,
                }
                try:
                    response_post = requests.post(WEBHOOK_URL, json=send_data)
                    if response_post.status_code == 200:
                        st.success("L'information a été envoyée avec succès au consultant IA.")
                        st.session_state.sent_messages.add(send_key)
                    else:
                        st.error(f"Échec de l'envoi de l'information. Statut: {response_post.status_code}")
                except Exception as e:
                    st.error(f"Erreur lors de l'envoi de l'information : {e}")
        else:
            st.write("✅ Information envoyée au consultant IA")
else:
    st.warning("Veuillez entrer votre nom, votre email et le nom de votre entreprise pour continuer.")
