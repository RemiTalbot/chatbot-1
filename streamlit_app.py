import streamlit as st
import requests
from openai import OpenAI
import time

WEBHOOK_URL = "https://hook.eu2.make.com/266bbw6u3mopx4g9jqizm9glnivc6dmu"
ASSISTANT_ID = "asst_5c4B9QMgs3gugmzkt4VdpKRJ"

st.title("💬 Audit IA")
st.write("La manière la plus simple de découvrir les applications potentielles de l'IA dans votre quotidien.")

# Ajout de l'explication sur l'objectif du bot
st.info("""
Ce bot est conçu pour vous aider à identifier des tâches dans votre quotidien qui prennent beaucoup de temps 
et apportent peu de valeur ajoutée, où l'IA pourrait potentiellement vous assister.
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
                st.success("Vos informations ont été envoyées avec succès.")
            else:
                st.error(f"Échec de l'envoi des informations. Statut: {response.status_code}")
        except Exception as e:
            st.error(f"Erreur lors de l'envoi des informations : {e}")
        st.session_state.info_sent = True

    openai_api_key = st.secrets["openai"]["api_key"] if "openai" in st.secrets else st.text_input("OpenAI API Key", type="password")
    
    if not openai_api_key:
        st.info("Veuillez ajouter votre clé API OpenAI pour continuer.", icon="🗝️")
    else:
        client = OpenAI(api_key=openai_api_key)

        if "thread_id" not in st.session_state:
            thread = client.beta.threads.create()
            st.session_state.thread_id = thread.id

        if "messages" not in st.session_state:
            st.session_state.messages = []
            # Ajout du message pré-enregistré
            st.session_state.messages.append({"role": "assistant", "content": "Présentez-vous et parlez-moi un peu de votre travail quotidien !"})

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

        if prompt := st.chat_input("Que souhaitez-vous savoir ?"):
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

            with st.spinner("L'assistant réfléchit..."):
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
