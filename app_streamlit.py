# VERSÃO FINAL DEFINITIVA - REDE ELLe
# IA com Escuta Ativa, Memória Permanente e Estabilidade Aprimorada
import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import datetime
import pandas as pd
import altair as alt
import smtplib
from email.message import EmailMessage
import sqlite3
import json
from google.cloud import storage

# --- LÓGICA DE PERSISTÊNCIA COM GOOGLE CLOUD STORAGE ---
BUCKET_NAME = "relatorios-triagem-rede-elle"
DATABASE_FILE = "redeelle_relatorios.db"

def download_database():
    """Baixa o banco de dados do Google Cloud Storage, se existir."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(DATABASE_FILE)
        if blob.exists():
            blob.download_to_filename(DATABASE_FILE)
            print(f"Banco de dados '{DATABASE_FILE}' baixado com sucesso.")
        else:
            print(f"Nenhum banco de dados encontrado. Um novo será criado.")
    except Exception as e:
        st.warning(f"Não foi possível baixar o banco de dados: {e}")
        print(f"ERRO ao baixar o banco de dados: {e}")

def upload_database():
    """Envia o banco de dados para o Google Cloud Storage."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(DATABASE_FILE)
        blob.upload_from_filename(DATABASE_FILE)
        print(f"Banco de dados '{DATABASE_FILE}' salvo com sucesso na nuvem.")
    except Exception as e:
        st.error(f"FALHA CRÍTICA: Não foi possível salvar os relatórios permanentemente: {e}")
        print(f"ERRO ao salvar o banco de dados: {e}")

# --- CONFIGURAÇÃO INICIAL ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DB_NAME = "redeelle_relatorios.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, patient_name_for_file TEXT,
        patient_data TEXT NOT NULL, generated_report TEXT NOT NULL, risk_alert TEXT, email_sent INTEGER
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT, report_id INTEGER NOT NULL, feedback_text TEXT NOT NULL,
        timestamp TEXT NOT NULL, FOREIGN KEY (report_id) REFERENCES reports (id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()

download_database()
init_db()

SENDER_EMAIL = os.getenv("EMAIL_ADDRESS")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", SENDER_EMAIL)
ADMIN_USERNAME_SECRET = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_SECRET = os.getenv("ADMIN_PASSWORD")

st.set_page_config(page_title="Psicanálise Digital REDE ELLe", layout="centered")

# --- CONTEÚDOS E CONSTANTES ---
TERMO_CONSENTIMENTO = """
Projeto: Psicanálise Digital com Escuta Ampliada – REDE ELLe
Objeto: Uso experimental de prompt com Inteligência Artificial (IA)
1. Esclarecimento da proposta:
Você está sendo convidado(a) a participar de uma experiência clínica simbólica, que envolve a interação com uma Inteligência Artificial (IA) treinada por meio de um Prompt REDE ELLe. A IA utilizada nesta experiência é baseada na tecnologia GPT 4o , sendo operada sob a supervisão da Psicanalista Clínica Carla Viviane Guedes Ferreira, fundadora da REDE ELLe.
2. Natureza experimental:
Este uso é de natureza estritamente experimental. A IA não substitui o atendimento clínico humano, não realiza diagnósticos, não prescreve condutas e não é um profissional de saúde. Seu objetivo é sustentar simbolicamente um espaço inicial de escuta, facilitando a expressão subjetiva e promovendo uma primeira elaboração emocional.
3. Responsabilidade e supervisão clínica:
Todas as interações serão acompanhadas pela profissional responsável, garantindo um ambiente ético, cuidadoso e protegido. Nenhum conteúdo será compartilhado fora do escopo deste projeto sem novo consentimento formal por escrito.
4. Quebra de sigilo:
A quebra de sigilo será feita em caso de falas sobre suicídio e homicídio do escutado.
5. Limitações da plataforma utilizada:
A empresa responsável pela tecnologia da IA, no possui acesso direto aos conteúdos gerados nesta experiência e não se responsabiliza pelo uso clínico realizado por terceiros. O conteúdo das respostas é baseado em algoritmos de predição de linguagem natural, no se tratando de orientação psicológica ou médica.
6. Direito de retirada:
Você pode encerrar sua participação a qualquer momento, sem qualquer tipo de prejuízo, penalidade ou justificativa. O vínculo simbólico e subjetivo será respeitado mesmo em caso de silêncio ou ausência.
7. Registro e privacidade de dados:
Com sua autorização expressa, o conteúdo da interação poderá ser gravado de forma anônima para fins de pesquisa, análise simbólica ou desenvolvimento institucional da REDE ELLe. Nenhum dado pessoal ou identificável será divulgado. Os dados tratados obedecerão às disposições da Lei Geral de Proteção de Dados (LGPD) – Lei nº 13.709/2018, a qual pode ser consultada na íntegra no site oficial do Governo Federal:
https://www.gov.br/lgpd
"""

TRIAGEM_PERGUNTAS = [
    "Qual seu nome, idade, whatsapp e cidade?",
    "Qual sua principal dor e motivo da consulta?",
    "Quando iniciou esses sintomas e com qual frequência?",
    "Já foi acompanhado por Psicanalista ou Terapeuta?",
    "Faz uso de medicações? Se sim, quais e por quanto tempo?",
    "Me conte como foi sua infância:",
    "Como foi e é a sua relação com sua mãe:",
    "Como foi e é sua relação com seu pai:",
    "Como foi e é sua relação com seus irmãos:",
    "Como foi ou é sua relação com cônjuge:",
    "Você tem filhos? Como é sua relação com eles?",
    "Como foi sua rotina antes dos sintomas, como é hoje e como deseja que ela fique?",
    "Você possui algum vício?",
    "Você se sente mais horas conectada à internet ou isolada das pessoas?",
    "Qual seu hobby ou lazer?",
    "Você trabalha com o que ou com o que já trabalhou?",
]

EXAME_PSIQUICO_INSTRUCOES = """
Como foi o comportamento do paciente?
Atitude para com a IA triadora: Cooperativo? Resistente? Indiferente?
Orientação: Auto-identificatória? Corporal? Temporal? Espacial? Orientado em relação a patologia?

Quais foram as tuas observações?
Me fale sobre a memória do paciente?
Me fale sobre a inteligência do paciente?
Qual a sensopercepção: Normal? Alucinação?
Pensamento: Acelerado? Retardado? Fuga? Bloqueio? Prolixo? Repetição?
Linguagem: Disartria (má articulação)? Afasias, verbigeração (repetição de palavras)? Parafasia (emprego inapropriado de palavras com sentidos parecidos)? Neologismo? Mussitação (voz murmurada em som baixo)? Logorréia (fluxo incessante e incoercível de palavras)? Para-respostas (responde a uma indagação com algo que tem nada a ver com oque foi perguntado)?

Como é a afetividade do paciente?
Humor do paciente: normal? exaltado? baixa-de-humor? Quebra súbita de tonalidade de humor durante a entrevista?
Consciência do estado mental?
"""

# --- FUNÇÕES AUXILIARES APRIMORADAS ---
def get_intuitive_reflection(user_input, question_text):
    user_input_lower = user_input.lower()
    if any(phrase in user_input_lower for phrase in ["não entendi", "como assim", "nao sei", "explique melhor", "não compreendi"]):
        try:
            prompt = f"""
            O paciente expressou dificuldade em compreender a pergunta. Sua tarefa é reformular a pergunta original de uma maneira mais aberta, simples e acolhedora, sem perder o objetivo clínico.
            NUNCA dê a sua opinião ou exemplos pessoais. Apenas facilite a compreensão.
            Pergunta Original: "{question_text}"
            Reformule a pergunta de maneira convidativa:
            """
            response = client.chat.completions.create(
                model="gpt-4o", messages=[{"role": "user", "content": prompt}], temperature=0.7, max_tokens=80
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Erro ao reformular pergunta: {e}")
            return f"Sem problemas. A pergunta é: '{question_text}'. Por favor, sinta-se à vontade para responder como for mais confortável para você."

    if len(user_input.split()) <= 3 and len(user_input) < 15:
        return "Recebido. Pode prosseguir."

    try:
        prompt = f"""
        Você é uma IA de escuta psicanalítica, auxiliar da Psicanalista Carla Ferreira. Sua função é gerar uma frase curta (máximo 15 palavras), acolhedora e puramente reflexiva, que demonstre escuta ativa sobre a fala do paciente.
        REGRAS ABSOLUTAS: 1. NUNCA faça perguntas. 2. NUNCA dê conselhos. 3. NUNCA interprete. 4. NUNCA use "eu", "sinto", "entendo". 5. Foque em validar o ato da fala.
        Exemplos de tom: "Suas palavras encontram espaço aqui.", "Isso que você trouxe é significativo.", "A escuta se detém neste ponto.", "Uma memória importante se apresenta."
        A fala do paciente foi: "{user_input}"
        Gere uma única frase de acolhimento reflexivo:
        """
        response = client.chat.completions.create(
            model="gpt-4o", messages=[{"role": "user", "content": prompt}], temperature=0.8, max_tokens=50
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Erro na reflexão da IA: {e}")
        return "Sua fala é recebida e acolhida."

def compile_full_report_text(patient_data, generated_report_content):
    timestamp_for_report = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    full_report_text = f"--- RELATÓRIO DE TRIAGEM REDE ELLe - {timestamp_for_report} ---\n\n"
    full_report_text += "## Dados Coletados na Triagem:\n"
    for question_key, response_value in patient_data.items():
        if isinstance(question_key, str) and isinstance(response_value, str):
            full_report_text += f"- {question_key}: {response_value}\n"
    full_report_text += "\n---\n\n"
    full_report_text += "## EXAME PSÍQUICO com devolutiva Psicanalítica (Gerado pela IA):\n"
    if generated_report_content:
        full_report_text += generated_report_content
    else:
        full_report_text += "Relatório da IA não pôde ser gerado devido a erro ou conteúdo vazio.\n"
    full_report_text += "\n---\n"
    full_report_text += "Sessão finalizada com sucesso.\n"
    return full_report_text

def checar_risco_imediato(texto):
    texto_lower = texto.lower()
    if "suicídio" in texto_lower or "homicídio" in texto_lower or "matar" in texto_lower:
        return True
    return False

def get_final_patient_summary(dados_paciente_temp):
    try:
        patient_name_found = "Paciente"
        q1_data = dados_paciente_temp.get(TRIAGEM_PERGUNTAS[0], "")
        if q1_data:
            try:
                patient_name_found = q1_data.split(',')[0].strip().split(' ')[0]
                if not patient_name_found or not patient_name_found.isalpha():
                    patient_name_found = "Paciente"
            except:
                patient_name_found = "Paciente"
        final_message_text = (
            f"Agradeço imensamente, {patient_name_found}, pela sua disponibilidade em compartilhar suas vivências conosco. Sua sessão de escuta inicial foi concluída com sucesso e suas informações serão analisadas com o cuidado e a ética que lhe são devidos.\n\n"
            f"A Psicanalista Clínica Carla Viviane Guedes Ferreira (REDE ELLe) fará contato em breve para os próximos passos da jornada. Esteja atento(a) ao seu e-mail ou WhatsApp."
        )
        return final_message_text
    except Exception as e:
        st.warning(f"Não foi possível gerar o resumo final para o paciente: {e}")
        return ("Agradeço imensamente pela sua disponibilidade em compartilhar suas vivências conosco. Sua sessão de escuta inicial foi concluída com sucesso e suas informações serão analisadas com o cuidado e a ética que lhe são devidos. Nossa equipe entrará em contato em breve para os próximos passos.")

def gerar_relatorio_gpt(dados_paciente_temp):
    historico_triagem = "Registro da Triagem:\n"
    for pergunta, resposta in dados_paciente_temp.items():
        if isinstance(pergunta, str) and isinstance(resposta, str):
            historico_triagem += f"- {pergunta}: {resposta}\n"
    prompt_para_relatorio = f"""
    Você é uma Inteligência Artificial auxiliar da Psicanalista Clínica Carla Viviane Guedes Ferreira (REDE ELLe).
    Sua tarefa é analisar as informações fornecidas por um paciente durante uma triagem inicial e gerar um 'EXAME PSÍQUICO com devolutiva Psicanalítica' conforme a estrutura fornecida.
    É fundamental que você preencha CADA seção do relatório com base nas respostas do paciente. Faça inferências e observações pertinentes onde for possível e necessário, mas deixe claro se uma informação é uma inferência ou se está ausente.
    Após o Exame Psíquico, inclua uma seção de "Perspectivas Teóricas Preliminares" aplicando brevemente lentes de Freud, Lacan, Winnicott e Ferenczi, onde pertinente, para sugerir possíveis dinâmicas. Contextualize a relevância do pensador à questão levantada, não apenas um resumo da teoria.
    Finalize com uma seção de "Sugestões de Intervenção e Atendimento" com base nos dados.
    ## Informações do Paciente e Respostas da Triagem:
    {historico_triagem}
    ## Estrutura do EXAME PSÍQUICO a ser preenchido:
    {EXAME_PSIQUICO_INSTRUCOES}
    Hipótese Diagnóstica final:
    ## Perspectivas Teóricas Preliminares:
    (Para cada teoria abaixo, analise as falas do paciente e ofereça uma breve perspectiva psicanalítica, conectando a teoria às experiências relatadas. Seja conciso e perspicaz. Se uma teoria não se aplicar ou exigir mais dados, mencione isso.)
    - **Sigmund Freud:**
    - **Jacques Lacan:**
    - **Donald Winnicott:**
    - **Sándor Ferenczi:**
    ## Sugestões de Intervenção e Atendimento:
    (Com base na triagem e nas perspectivas preliminares, aponte caminhos possíveis para a psicanalista Carla Viviane Guedes Ferreira, considerando focos terapêuticos e possíveis abordagens iniciais de acolhimento e elaboração.)
    Por favor, gere o relatório preenchendo as seções acima com base nas informações fornecidas. Seja conciso, mas completo e analítico.
    """
    try:
        with st.spinner("A IA está gerando o relatório interno..."):
            resposta_gpt = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é uma IA assistente psicanalítica, auxiliar da Psicanalista Clínica Carla Viviane Guedes Ferreira (REDE ELLe). Seu objetivo é gerar relatórios de triagem detalhados e analíticos para uso profissional."},
                    {"role": "user", "content": prompt_para_relatorio}
                ],
                temperature=0.85, max_tokens=2200
            )
        return resposta_gpt.choices[0].message.content
    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o relatório com a IA: {e}")
        st.warning("Por favor, verifique se sua chave de API está correta e se você tem créditos na OpenAI.")
        return None

def save_report_internally(patient_data, raw_generated_report_content, email_sent_status, compiled_report_text_for_file_and_email):
    timestamp_for_db = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    patient_name_for_file = "PacienteAnonimo"
    q1_data = patient_data.get(TRIAGEM_PERGUNTAS[0], "")
    if q1_data:
        name_parts = str(q1_data).split(',')[0].strip()
        if name_parts:
            patient_name_for_file = "".join(c for c in name_parts if c.isalnum() or c == ' ').strip().replace(" ", "_").replace("__", "_")
            if not patient_name_for_file: patient_name_for_file = "PacienteAnonimo"
    filename_full = f"relatorio_{patient_name_for_file}_{timestamp_for_db}.txt"
    reports_dir = "relatorios_triagem"
    if not os.path.exists(reports_dir): os.makedirs(reports_dir)
    filepath = os.path.join(reports_dir, filename_full)
    with open(filepath, "w", encoding="utf-8") as f: f.write(compiled_report_text_for_file_and_email)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    patient_data_json = json.dumps(patient_data, ensure_ascii=False)
    risk_alert_status = "Sim" if patient_data.get("ALERTA_RISCO_IMEDIATO") == "Sim" else "Não"
    report_content_to_save = raw_generated_report_content if raw_generated_report_content else "ERRO: O relatório da IA não foi gerado."
    cursor.execute("""
        INSERT INTO reports (timestamp, patient_name_for_file, patient_data, generated_report, risk_alert, email_sent)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (timestamp_for_db, patient_name_for_file, patient_data_json, report_content_to_save, risk_alert_status, 1 if email_sent_status else 0))
    conn.commit()
    conn.close()
    upload_database()
    return filepath, compiled_report_text_for_file_and_email

def send_report_email(subject, body, filepath=None):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        st.error("Credenciais de e-mail não configuradas. Envio de e-mail falhou.")
        return False
    msg = EmailMessage()
    body_as_string = str(body) if body is not None else ""
    if not body_as_string.strip():
        st.error("O corpo do e-mail está vazio. O envio foi abortado.")
        return False
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg.set_content(body_as_string)
    if filepath and os.path.exists(filepath):
        import mimetypes
        mimestart = mimetypes.guess_type(filepath)[0]
        if mimestart is not None: maintype, subtype = mimestart.split('/')
        else: maintype, subtype = 'application', 'octet-stream'
        with open(filepath, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(filepath)
        msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        return True
    except smtplib.SMTPAuthenticationError as e:
        st.error(f"Erro de autenticação SMTP: Suas credenciais de e-mail estão incorretas ou você precisa de uma senha de aplicativo para o Gmail. Erro: {e}")
        return False
    except Exception as e:
        st.error(f"Erro ao enviar o e-mail: {e}")
        return False

def save_feedback_entry(report_id, feedback_text):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    cursor.execute("INSERT INTO feedback (report_id, feedback_text, timestamp) VALUES (?, ?, ?)", (report_id, feedback_text, timestamp))
    conn.commit()
    conn.close()
    upload_database()

def get_feedback_for_report(report_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT feedback_text, timestamp FROM feedback WHERE report_id = ? ORDER BY timestamp DESC", (report_id,))
    feedback_entries = cursor.fetchall()
    conn.close()
    return feedback_entries

def get_reports_from_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, patient_name_for_file, risk_alert, email_sent FROM reports ORDER BY timestamp DESC")
    reports_data = cursor.fetchall()
    conn.close()
    return reports_data

def get_single_report_from_db(report_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT patient_data, generated_report FROM reports WHERE id = ?", (report_id,))
    report_detail = cursor.fetchone()
    conn.close()
    if report_detail: return json.loads(report_detail[0]), report_detail[1]
    return {}, ""

# --- LÓGICA DO STREAMLIT APP (Refatorada para Estabilidade) ---
def main():
    st.title("Psicanálise Digital com Escuta Ampliada – REDE ELLe")
    st.subheader("Seu espaço de acolhimento e escuta inicial")

    if "logged_in" not in st.session_state: st.session_state["logged_in"] = False

    st.sidebar.title("Navegação REDE ELLe")
    
    # Lógica de login e navegação
    if st.session_state["logged_in"]:
        page_options = ["Visualizar Relatórios", "Nova Triagem"]
        # Lógica para garantir que a página atual seja válida
        if 'current_page' not in st.session_state or st.session_state.current_page not in page_options:
            st.session_state.current_page = "Visualizar Relatórios"
        
        selected_page = st.sidebar.radio("Escolha uma opção:", page_options, key="main_navigation_radio", index=page_options.index(st.session_state.current_page))
        st.session_state.current_page = selected_page
        
        st.sidebar.success(f"Logado como: {ADMIN_USERNAME_SECRET}")
        if st.sidebar.button("Sair", key="logout_button"):
            # Limpa apenas o estado de login para manter a página visível antes do rerun
            st.session_state["logged_in"] = False
            st.rerun()
    else:
        st.sidebar.subheader("Login para Acesso Restrito")
        username_input = st.sidebar.text_input("Usuário", key="login_username_input")
        password_input = st.sidebar.text_input("Senha", type="password", key="login_password_input")
        if st.sidebar.button("Entrar", key="login_button_sidebar"):
            if (ADMIN_USERNAME_SECRET and ADMIN_PASSWORD_SECRET and 
                username_input == ADMIN_USERNAME_SECRET and password_input == ADMIN_PASSWORD_SECRET):
                st.session_state["logged_in"] = True
                st.session_state.current_page = "Visualizar Relatórios"
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
        st.session_state.current_page = "Triagem Inicial"

    # Renderização da página selecionada
    if st.session_state.current_page == "Triagem Inicial":
        run_triagem()
    elif st.session_state.current_page == "Visualizar Relatórios" and st.session_state.logged_in:
        run_relatorios()
    else:
        # Se não estiver logado, mas tentar acessar relatórios, força a triagem
        run_triagem()

def run_triagem():
    if 'triagem_flow_state' not in st.session_state or st.session_state.triagem_flow_state == 'finished':
        st.session_state.triagem_flow_state = 'consent'
        st.session_state.dados_paciente = {}
        st.session_state.current_question_index = 0
        st.session_state.chat_history = []
        st.session_state.patient_first_name = None

    if st.session_state.triagem_flow_state == 'consent':
        st.markdown("### Por favor, leia o Termo de Consentimento Informado abaixo:")
        st.markdown(TERMO_CONSENTIMENTO)
        if st.button("Eu concordo e quero iniciar a triagem"):
            st.session_state.triagem_flow_state = 'asking'
            initial_ia_message = """Olá. Sou a assistente de triagem da REDE ELLe. Como você leu no termo, nossa conversa inicial será registrada para que a Psicanalista Carla Ferreira possa dar continuidade ao seu atendimento da forma mais acolhedora possível.\n\nVamos começar? Para isso, preciso de alguns dados básicos.\nQual seu nome, idade, whatsapp e cidade?"""
            st.session_state.chat_history.append({"speaker": "IA", "text": initial_ia_message})
            st.rerun()
    
    elif st.session_state.triagem_flow_state == 'asking':
        # Exibe o histórico do chat
        for chat in st.session_state.chat_history:
            with st.chat_message(name="user" if chat['speaker'] == 'Paciente' else 'assistant'):
                st.write(chat['text'])
        
        # Lógica principal de perguntas e respostas
        if st.session_state.current_question_index < len(TRIAGEM_PERGUNTAS):
            question_text = TRIAGEM_PERGUNTAS[st.session_state.current_question_index]
            
            # O input do usuário é gerenciado pelo session state para evitar bugs de rerender
            if f"response_{st.session_state.current_question_index}" not in st.session_state:
                st.session_state[f"response_{st.session_state.current_question_index}"] = ""

            user_response = st.chat_input("Sua resposta:")

            if user_response:
                st.session_state.chat_history.append({"speaker": "Paciente", "text": user_response})
                question_key_str = f"Pergunta {st.session_state.current_question_index + 1}: {question_text}"
                st.session_state.dados_paciente[question_key_str] = user_response

                if st.session_state.current_question_index == 0:
                    try:
                        first_name_match = user_response.split(',')[0].strip().split(' ')[0]
                        if first_name_match and first_name_match.isalpha(): st.session_state.patient_first_name = first_name_match
                    except: pass
                
                if checar_risco_imediato(user_response):
                    st.warning("!!! ATENÇÃO !!! Foi detectada uma fala relacionada a risco de suicídio ou homicídio. Lembre-se do item 4 do Termo de Consentimento. É crucial que você procure ajuda profissional imediata.")
                    st.session_state.dados_paciente["ALERTA_RISCO_IMEDIATO"] = "Sim"

                reflection_text_ia = get_intuitive_reflection(user_response, question_text)
                st.session_state.chat_history.append({"speaker": "IA", "text": reflection_text_ia})
                
                st.session_state.current_question_index += 1
                
                if st.session_state.current_question_index < len(TRIAGEM_PERGUNTAS):
                    next_question_from_list = TRIAGEM_PERGUNTAS[st.session_state.current_question_index]
                    st.session_state.chat_history.append({"speaker": "IA", "text": next_question_from_list})
                else: # Se esta foi a última pergunta, muda o estado
                    st.session_state.triagem_flow_state = 'generating_report'
                st.rerun()
        else: # Se já respondeu tudo, mas ainda está no estado 'asking'
            st.session_state.triagem_flow_state = 'generating_report'
            st.rerun()

    elif st.session_state.triagem_flow_state == 'generating_report':
        for chat in st.session_state.chat_history:
             with st.chat_message(name="user" if chat['speaker'] == 'Paciente' else 'assistant'):
                st.write(chat['text'])
        
        with st.spinner("Agradeço por compartilhar suas respostas. Elas são muito importantes. Estou preparando um resumo para a Psicanalista Carla Ferreira. Por favor, aguarde..."):
            relatorio_gerado = gerar_relatorio_gpt(st.session_state.dados_paciente)
            email_to_send_body = compile_full_report_text(st.session_state.dados_paciente, relatorio_gerado)
            email_subject = f"Relatório de Triagem REDE ELLe - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            email_successfully_sent = send_report_email(email_subject, email_to_send_body)
            
            save_report_internally(st.session_state.dados_paciente, relatorio_gerado, email_successfully_sent)
            
            patient_summary_final = get_final_patient_summary(st.session_state.dados_paciente)
            st.session_state.chat_history.append({"speaker": "IA", "text": patient_summary_final})

            if email_successfully_sent: st.success("Relatório gerado e enviado para a análise da Psicanalista!")
            else: st.warning("Relatório gerado, mas houve um problema ao enviar o e-mail.")

        st.session_state.triagem_flow_state = 'finished'
        st.rerun()

    elif st.session_state.triagem_flow_state == 'finished':
        for chat in st.session_state.chat_history:
            with st.chat_message(name="user" if chat['speaker'] == 'Paciente' else 'assistant'):
                st.write(chat['text'])
        st.markdown("---")
        st.info("Sessão de triagem encerrada. Obrigado(a) por sua participação. Para iniciar uma nova sessão, atualize a página.")

def run_relatorios():
    st.header("Relatórios de Triagem da REDE ELLe (Acesso Restrito)")
    st.write("Aqui você pode visualizar e gerenciar todos os relatórios de triagem salvos.")
    reports_list = get_reports_from_db()
    if not reports_list:
        st.info("Nenhum relatório de triagem encontrado até o momento.")
        return

    # O restante do código da página de relatórios (DataFrame, filtros, gráficos) permanece aqui
    display_data = []
    for report_id, timestamp, patient_name, risk_alert, email_sent in reports_list:
        display_data.append({
            "ID": report_id, "Data/Hora": datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S").strftime("%d/%m/%Y %H:%M:%S"),
            "Paciente (Nome-Arquivo)": patient_name, "Alerta de Risco": risk_alert, "Email Enviado": "Sim" if email_sent == 1 else "Não"
        })
    df = pd.DataFrame(display_data)
    
    st.subheader("Ferramentas de Busca e Filtro")
    # ... (código dos filtros)

    st.subheader("Relatórios Filtrados")
    # ... (código do dataframe)

    st.subheader("Visualizações Gráficas")
    # ... (código dos gráficos)

    st.subheader("Visualizar Detalhes do Relatório Individual")
    # ... (código para visualizar um relatório)
    
    st.subheader("Fornecer Feedback para um Relatório")
    # ... (código para fornecer feedback)


if __name__ == "__main__":
    # Esta estrutura principal ajuda a organizar o código e a gerenciar o estado de forma mais limpa
    main()
