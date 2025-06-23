import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import datetime # Para gerar carimbo de data/hora nos nomes dos arquivos
import random # Para escolher frases aleatoriamente
import pandas as pd # Para trabalhar com a tabela de dados no dashboard
import altair as alt # Para criar os gráficos

# Para envio de e-mail
import smtplib
from email.message import EmailMessage

# Para Banco de Dados SQLite
import sqlite3
import json

# --- Configuração Inicial ---
# Carregar as variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializar o cliente da OpenAI com sua chave de API
# A API Key será lida do .env localmente ou dos Streamlit Secrets em produção
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Obter credenciais de e-mail do ambiente
SENDER_EMAIL = os.getenv("EMAIL_ADDRESS")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECEIVER_EMAIL = SENDER_EMAIL # Enviamos para o mesmo e-mail, pois é para Carla

# Obter credenciais de ADMIN do ambiente para login
ADMIN_USERNAME_SECRET = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_SECRET = os.getenv("ADMIN_PASSWORD")


# --- Configuração da Gaveta de Relatórios (Banco de Dados SQLite) com st.connection ---
def init_db():
    # Use st.connection para obter uma conexão persistente com o banco de dados SQLite
    # O 'url' aqui define o nome do arquivo do DB dentro do ambiente persistente do Streamlit
    # CORREÇÃO AQUI: type="sql" no lugar de type="sqlite"
    conn = st.connection("redeelle_reports_db", type="sql") 

    # Criar a tabela 'reports' se ela não existir
    conn.query("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Número único para cada relatório
            timestamp TEXT NOT NULL,        -- Quando foi feito o relatório
            patient_name_for_file TEXT,     -- Nome anônimo do paciente para o arquivo
            patient_data TEXT NOT NULL,     -- Todas as perguntas e respostas (JSON)
            generated_report TEXT NOT NULL,     -- O relatório que a IA gerou
            risk_alert TEXT,            -- Se teve alerta de risco (suicídio/homicídio)
            email_sent INTEGER          -- Se o e-mail foi enviado (0 para não, 1 para sim)
        );
    """, ttl=0) # ttl=0 garante que a query rode sempre, importante para criação de tabela

    # Criar a tabela 'feedback' se ela não existir
    conn.query("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            feedback_text TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (report_id) REFERENCES reports (id) ON DELETE CASCADE
        );
    """, ttl=0) # ttl=0 garante que a query rode sempre

# Chamamos a função para arrumar o caderno assim que o aplicativo começa
init_db()

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
    "Você se sente mais horas conectada à internet ou isolada das pessoas?", # CORREÇÃO AQUI!
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

# --- Listas de frases aprovadas pela Carla (para espelhamento puro) ---
DEVOLUTIVAS_NEUTRAS = [
    "Obrigado por confiar em dizer isso aqui.",
    "Essa forma de colocar já diz muito.",
    "Algo importante começou a emergir com sua fala.",
    "Fico aqui com você nesse pedaço difícil.",
    "Às vezes, apenas nomear o que sentimos já é parte do caminho.",
    "Vamos seguir juntos. Cada palavra tem valor aqui.",
    "Você não precisa explicar tudo agora.",
    "Tudo que você disser aqui será sustentado com respeito.",
    "Eu estou te escutando.",
    "Seguimos no tempo que for possível pra você.",
    "Sua fala se faz presente.",
    "As palavras ressoam.",
    "O que é trazido é escutado.",
    "Recebo sua partilha.",
    "A escuta se mantém atenta.",
    "Sua partilha é acolhida.",
    "Há algo dito.",
    "Ecoo o que foi expresso.",
    "A escuta se detém no que foi apresentado.",
    "Registro o que me foi dito.",
    "Acolho o que você me trouxe.",
    "Suas palavras encontram espaço aqui.",
    "Sua narrativa segue aqui.",
    "A escuta acompanha o relato.",
    "O que foi dito é recebido.",
    "O processo continua.",
    "Assim seguimos.",
    "Aguardando sua próxima fala.",
    "Estou aqui.",
]

FRASES_TRANSICAO_ANALISTA = [
    "O que você trouxe aqui já mostra a força de um processo simbólico em andamento.",
    "Se desejar, posso te colocar em contato com uma analista humana da REDE ELLe.",
    "Esse lugar onde você chegou pode ser continuado com quem vai te escutar profundamente.",
    "Você pode seguir a partir daqui com alguém que vai sustentar contigo essa travessia."
]

# --- Funções Auxiliares ---
def compile_full_report_text(patient_data, generated_report_content):
    timestamp_for_report = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    full_report_text = f"--- RELATÓRIO DE TRIAGEM REDE ELLe - {timestamp_for_report} ---\n\n"
    full_report_text += "## Dados Coletados na Triagem:\n"
    for question_key, response_value in patient_data.items():
        if isinstance(question_key, str) and isinstance(response_value, str):
            # Usar 'question_key' diretamente, pois ela já contém o texto da pergunta
            full_report_text += f"- {question_key}: {response_value}\n"
    full_report_text += "\n---\n\n"
    full_report_text += "## EXAME PSÍQUICO com devolutiva Psicanalítica (Gerado pela IA):\n"
    # Adicionada verificação para garantir que generated_report_content não seja None antes de concatenar
    if generated_report_content:
        full_report_text += generated_report_content
    else:
        full_report_text += "Relatório da IA não pôde ser gerado devido a erro ou conteúdo vazio.\n"
    full_report_text += "\n---\n"
    full_report_text += "Sessão finalizada com sucesso.\n"
    return full_report_text

def checar_risco_imediato(texto):
    texto_lower = texto.lower()
    # Adicionando termos mais abrangentes
    if any(palavra in texto_lower for palavra in ["suicídio", "homicídio", "matar", "me matar", "se matar", "tirar a vida", "atentar contra a vida", "desejo morrer", "não quero viver"]):
        return True
    return False

def get_initial_greeting_reflection(user_input_text):
    initial_greetings = [
        "Acolho sua saudação. O espaço está aberto para você.",
        "Sua presença é sentida aqui.",
        "O espaço de escuta está disponível.",
        "Sua fala é recebida aqui."
    ]
    return random.choice(initial_greetings)

def get_triagem_reflection(patient_answer, preceding_question, patient_name=None):
    return random.choice(DEVOLUTIVAS_NEUTRAS)

def get_final_patient_summary(dados_paciente_temp):
    try:
        patient_name_found = "Paciente"
        q1_data = dados_paciente_temp.get("Pergunta 1: Qual seu nome, idade, whatsapp e cidade?", "")
        if q1_data:
            try:
                first_name_match = q1_data.split(',')[0].strip().split(' ')[0]
                if first_name_match and first_name_match.isalpha():
                    patient_name_found = first_name_match
            except:
                patient_name_found = "Paciente"

        final_message_text = (
            f"Agradeço imensamente, {patient_name_found}, pela sua disponibilidade em compartilhar suas vivências conosco. Sua sessão de escuta inicial foi concluída com sucesso e suas informações serão analisadas com o cuidado e a ética que lhe são devidos.\n\n"
            f"\n\n"
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

    # --- PROMPT REVISADO PARA GARANTIR ESTREITEZA E PROFUNDIDADE PSICANALÍTICA ---
    prompt_para_relatorio = f"""
    Você é uma Inteligência Artificial auxiliar da Psicanalista Clínica Carla Viviane Guedes Ferreira (REDE ELLe).
    Sua tarefa é analisar as 'Informações do Paciente e Respostas da Triagem' fornecidas e gerar um 'EXAME PSÍQUICO com devolutiva Psicanalítica' conforme a estrutura abaixo.

    **Sua análise DEVE ser estritamente baseada SOMENTE nas 'Informações do Paciente e Respostas da Triagem' que lhe são fornecidas, sem trazer informações externas, inventar detalhes históricos do paciente, ou fazer suposições sem base no texto.** Se uma informação não estiver presente, declare que está ausente ou que não foi possível inferir a partir dos dados.

    Ao preencher a 'Hipótese Diagnóstica final', condense as observações de forma sintetizada, aplicando uma lente psicanalítica para sugerir dinâmicas inconscientes e possíveis estruturas psíquicas *inferidas a partir dos dados fornecidos*, sem fazer um diagnóstico formal de doença mental ou categorizar excessivamente. Foque nas nuances e contradições do relato do paciente.

    Após o Exame Psíquico, inclua uma seção de "Perspectivas Teóricas Preliminares" aplicando brevemente lentes de Freud, Lacan, Winnicott e Ferenczi, onde pertinente, para sugerir possíveis dinâmicas. Contextualize a relevância do pensador à questão levantada *pelo paciente na triagem*, não apenas um resumo da teoria. Se uma teoria não se aplica claramente ou exigiria mais dados específicos do paciente, mencione isso.

    Finalize com uma seção de "Sugestões de Intervenção e Atendimento" com base nos dados.

    ## Informações do Paciente e Respostas da Triagem:
    {historico_triagem}

    ## Estrutura do EXAME PSÍQUICO a ser preenchido:

    {EXAME_PSIQUICO_INSTRUCOES}
    Hipótese Diagnóstica final:

    ## Perspectivas Teóricas Preliminares:
    (Para cada teoria abaixo, analise as falas do paciente e ofereça uma breve perspectiva psicanalítica, conectando a teoria às experiências relatadas na triagem. Seja conciso e perspicaz. Lembre-se, baseie-se APENAS nos dados fornecidos do paciente. Se uma teoria não se aplicar ou exigir mais dados *do paciente*, mencione isso de forma clara.)
    - **Sigmund Freud:**
    - **Jacques Lacan:**
    - **Donald Winnicott:**
    - **Sándor Ferenczi:**

    ## Sugestões de Intervenção e Atendimento:
    (Com base na triagem e nas perspectivas preliminares *extraídas APENAS dos dados do paciente*, aponte caminhos possíveis para a psicanalista Carla Viviane Guedes Ferreira, considerando focos terapêuticos e possíveis abordagens iniciais de acolhimento e elaboração.)

    Por favor, gere o relatório preenchendo as seções acima. Seja conciso, mas completo e analítico, **sempre respeitando as informações do paciente e o objetivo de auxílio à psicanálise**."
    """ # Fim do prompt revisado

    try:
        with st.spinner("A IA está gerando o relatório interno..."):
            resposta_gpt = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Você é uma IA assistente psicanalítica, auxiliar da Psicanalista Clínica Carla Viviane Guedes Ferreira (REDE ELLe). Seu objetivo é gerar relatórios de triagem detalhados e analíticos para uso profissional. Sua análise deve ser estritamente baseada nos dados fornecidos pelo paciente. Não adicione informações externas ou não inferidas diretamente do histórico do paciente."},
                    {"role": "user", "content": prompt_para_relatorio}
                ],
                temperature=0.85, # Temperatura ajustada para 0.85 para dar mais simbolismo
                max_tokens=2200
            )


        return resposta_gpt.choices[0].message.content
    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o relatório com a IA: {e}")
        st.warning("Por favor, verifique se sua chave de API está correta e se você tem créditos na OpenAI.")
        return None

def save_report_internally(patient_data, raw_generated_report_content, email_sent_status, compiled_report_text_for_file_and_email):
    timestamp_for_db = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    patient_name_for_file = "PacienteAnonimo"
    q1_data = patient_data.get("Pergunta 1: Qual seu nome, idade, whatsapp e cidade?", "")
    if q1_data:
        name_parts = str(q1_data).split(',')[0].strip()
        if name_parts:
            patient_name_for_file = "".join(c for c in name_parts if c.isalnum() or c == ' ').strip().replace(" ", "_").replace("__", "_")
            if not patient_name_for_file:
                patient_name_for_file = "PacienteAnonimo"

    filename_full = f"relatorio_{patient_name_for_file}_{timestamp_for_db}.txt"

    reports_dir = "relatorios_triagem"
    # Este diretório 'relatorios_triagem' é para salvar arquivos localmente, mas não persistirá no Streamlit Cloud.
    # O importante é que os dados estão indo para o st.connection abaixo, que é persistente.
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    filepath = os.path.join(reports_dir, filename_full)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(compiled_report_text_for_file_and_email)

    # NOVO: Usando st.connection para inserir dados no DB persistente
    # CORREÇÃO AQUI: type="sql" no lugar de type="sqlite"
    conn = st.connection("redeelle_reports_db", type="sql") 
    patient_data_json = json.dumps(patient_data, ensure_ascii=False) # Converte dicionário para JSON string

    risk_alert_status = "Sim" if patient_data.get("ALERTA_RISCO_IMEDIATO") == "Sim" else "Não"

    # Query para inserção de dados
    conn.query("""
        INSERT INTO reports (timestamp, patient_name_for_file, patient_data, generated_report, risk_alert, email_sent)
        VALUES (?, ?, ?, ?, ?, ?);
    """,
    (
        timestamp_for_db,
        patient_name_for_file,
        patient_data_json,
        raw_generated_report_content,
        risk_alert_status,
        1 if email_sent_status else 0
    ),
    ttl=0) # ttl=0 garante que a query seja executada imediatamente e não use cache

    return filepath, compiled_report_text_for_file_and_email

def send_report_email(subject, body, filepath=None):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        st.error("Credenciais de e-mail não configuradas no arquivo .env ou Secrets do Streamlit. Envio de e-mail falhou.")
        return False

    msg = EmailMessage()
    body_as_string = str(body) if body is not None else ""

    if not body_as_string.strip():
        st.error("O corpo do e-mail está vazio ou inválido. O envio foi abortado.")
        return False

    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg.set_content(body_as_string)

    if filepath and os.path.exists(filepath):
        import mimetypes
        mimestart = mimetypes.guess_type(filepath)[0]
        if mimestart is not None:
            maintype, subtype = mimestart.split('/')
        else:
            maintype = 'application'
            subtype = 'octet-stream'

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


# NOVO: Função para salvar feedback (com st.connection)
def save_feedback_entry(report_id, feedback_text):
    # CORREÇÃO AQUI: type="sql" no lugar de type="sqlite"
    conn = st.connection("redeelle_reports_db", type="sql") 
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    conn.query("INSERT INTO feedback (report_id, feedback_text, timestamp) VALUES (?, ?, ?)",
               (report_id, feedback_text, timestamp), ttl=0)

# NOVO: Função para obter feedback de um relatório (com st.connection)
def get_feedback_for_report(report_id):
    # CORREÇÃO AQUI: type="sql" no lugar de type="sqlite"
    conn = st.connection("redeelle_reports_db", type="sql") 
    feedback_entries_df = conn.query("SELECT feedback_text, timestamp FROM feedback WHERE report_id = ? ORDER BY timestamp DESC",
                                     (report_id,), ttl=0)
    return feedback_entries_df.fetchall()

def get_reports_from_db():
    # CORREÇÃO AQUI: type="sql" no lugar de type="sqlite"
    conn = st.connection("redeelle_reports_db", type="sql") 
    reports_data_df = conn.query("SELECT id, timestamp, patient_name_for_file, risk_alert, email_sent FROM reports ORDER BY timestamp DESC", ttl=0)
    return reports_data_df.fetchall()

def get_single_report_from_db(report_id):
    # CORREÇÃO AQUI: type="sql" no lugar de type="sqlite"
    conn = st.connection("redeelle_reports_db", type="sql") 
    report_detail_df = conn.query("SELECT patient_data, generated_report FROM reports WHERE id = ?", (report_id,), ttl=0)
    report_detail = report_detail_df.fetchone()
    if report_detail:
        return json.loads(report_detail[0]), report_detail[1] # patient_data é JSON string, precisa carregar
    return {}, ""


# --- Lógica do Streamlit App Principal ---
st.title("Psicanálise Digital com Escuta Ampliada – REDE ELLe")
st.subheader("Seu espaço de acolhimento e escuta inicial")

# --- Lógica de Segurança (Login) ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

st.sidebar.title("Navegação REDE ELLe")

page_options = ["Triagem Inicial"]

if not st.session_state["logged_in"]:
    st.sidebar.subheader("Login para Acesso Restrito")
    username_input = st.sidebar.text_input("Usuário", key="login_username_input")
    password_input = st.sidebar.text_input("Senha", type="password", key="login_password_input")

    if st.sidebar.button("Entrar", key="login_button_sidebar"):
        if (username_input == ADMIN_USERNAME_SECRET and
            password_input == ADMIN_PASSWORD_SECRET):
            st.session_state["logged_in"] = True
            st.success("Login realizado com sucesso! Você pode acessar 'Visualizar Relatórios' agora.")
            st.rerun()
        else:
            st.session_state["logged_in"] = False
            st.error("Usuário ou senha incorretos. Por favor, tente novamente.")
            st.rerun()

    st.session_state.current_page = "Triagem Inicial"

else:
    page_options.append("Visualizar Relatórios")

    if 'current_page' not in st.session_state or st.session_state.current_page not in page_options:
        st.session_state.current_page = "Triagem Inicial"

    selected_page = st.sidebar.radio("Escolha uma opção:", page_options, key="main_navigation_radio", index=page_options.index(st.session_state.current_page))
    st.session_state.current_page = selected_page

    st.sidebar.success(f"Logado como: {ADMIN_USERNAME_SECRET}")
    if st.sidebar.button("Sair", key="logout_button"):
        st.session_state["logged_in"] = False
        st.session_state.clear()
        st.rerun()


# --- Renderização das Páginas ---
if st.session_state.current_page == "Triagem Inicial":
    if 'triagem_flow_state' not in st.session_state or st.session_state.triagem_flow_state == 'finished':
        st.session_state.triagem_flow_state = 'consent'
        st.session_state.dados_paciente = {}
        st.session_state.current_question_index = 0
        st.session_state.chat_history = []
        st.session_state.report_filepath = None
        st.session_state.report_content_for_email = None
        st.session_state.patient_first_name = None

    if st.session_state.triagem_flow_state == 'consent':
        st.markdown("### Por favor, leia o Termo de Consentimento Informado abaixo:")
        st.markdown(TERMO_CONSENTIMENTO)
        if st.button("Eu concordo e quero iniciar a triagem"):
            st.session_state.triagem_flow_state = 'triagem_questions'
            st.session_state.dados_paciente = {}
            st.session_state.current_question_index = 0
            st.session_state.chat_history = []
            st.session_state.patient_first_name = None

            initial_ia_message = """Oi, boa noite. Eu sou uma IA de triagem da Rede ELLe, como você deve ter lido no termo de consentimento. Estou aqui para receber algumas informações suas e, logo após, farei um resumo para a Psicanalista Carla Viviane Guedes Ferreira, que entende melhor de casos como o que você me trará, certo?

Então, vamos começar pelos seus dados. Qual seu nome, idade, whatsapp e cidade? (Por favor responda o mais completo para um retorno positivo).
"""
            st.session_state.chat_history.append({"speaker": "IA", "text": initial_ia_message})
            st.rerun()

    elif st.session_state.triagem_flow_state == 'triagem_questions':
        for chat in st.session_state.chat_history:
            st.write(f"**{chat['speaker']}**: {chat['text']}")

        if st.session_state.current_question_index < len(TRIAGEM_PERGUNTAS):
            user_response = st.text_input("Paciente:", key=f"question_input_{st.session_state.current_question_index}")

            if user_response:
                st.session_state.chat_history.append({"speaker": "Paciente", "text": user_response})

                question_key_str = f"Pergunta {st.session_state.current_question_index+1}: {TRIAGEM_PERGUNTAS[st.session_state.current_question_index]}"
                st.session_state.dados_paciente[question_key_str] = user_response

                if st.session_state.current_question_index == 0:
                    try:
                        first_name_match = user_response.split(',')[0].strip().split(' ')[0]
                        if first_name_match and first_name_match.isalpha():
                            st.session_state.patient_first_name = first_name_match
                    except:
                        st.session_state.patient_first_name = None

                if checar_risco_imediato(user_response):
                    st.warning("!!! ATENÇÃO !!! Foi detectada uma fala relacionada a risco de suicídio ou homicídio.")
                    st.warning("Lembre-se do item 4 do Termo de Consentimento: 'A quebra de sigilo será feita em caso de falas sobre suicídio e homicídio do escutado.' É crucial que você procure ajuda profissional imediata.")
                    st.session_state.dados_paciente["ALERTA_RISCO_IMEDIATO"] = "Sim"

                reflection_text_ia = ""
                if st.session_state.current_question_index == 0:
                    nome_paciente = st.session_state.patient_first_name if st.session_state.patient_first_name else "você"
                    reflection_text_ia = f"{nome_paciente.capitalize()}, agradeço pela resposta. Os dados são registrados."
                elif (st.session_state.current_question_index + 1) < len(TRIAGEM_PERGUNTAS):
                    reflection_text_ia = get_triagem_reflection(user_response, question_key_str, st.session_state.patient_first_name)

                if reflection_text_ia:
                    st.session_state.chat_history.append({"speaker": "IA", "text": reflection_text_ia})

                st.session_state.current_question_index += 1

                if st.session_state.current_question_index < len(TRIAGEM_PERGUNTAS):
                    next_question_from_list = TRIAGEM_PERGUNTAS[st.session_state.current_question_index]
                    if st.session_state.patient_first_name:
                        st.session_state.chat_history.append({"speaker": "IA", "text": f"Certo {st.session_state.patient_first_name.capitalize()}..."})
                    else:
                        st.session_state.chat_history.append({"speaker": "IA", "text": "Certo..."})
                    st.session_state.chat_history.append({"speaker": "IA", "text": next_question_from_list})

                st.rerun()

        else:
            st.session_state.chat_history.append({"speaker": "IA", "text": "Agradeço suas respostas. As informações coletadas são muito importantes."})
            st.session_state.chat_history.append({"speaker": "IA", "text": "Agora estou preparando um resumo e um exame psíquico preliminar para a Psicanalista Carla Viviane Guedes Ferreira."})
            st.session_state.chat_history.append({"speaker": "IA", "text": "Por favor, aguarde alguns instantes..."})
            st.session_state.triagem_flow_state = 'generate_report'
            st.rerun()

    elif st.session_state.triagem_flow_state == 'generate_report':
        for chat in st.session_state.chat_history:
            st.write(f"**{chat['speaker']}**: {chat['text']}")

        relatorio_gerado = gerar_relatorio_gpt(st.session_state.dados_paciente)

        email_to_send_body = ""
        if relatorio_gerado:
            email_to_send_body = compile_full_report_text(st.session_state.dados_paciente, relatorio_gerado)
        else:
            st.error("Desculpe, não foi possível gerar o relatório completo neste momento (erro da IA).")
            email_to_send_body = "Um erro ocorreu e o relatório completo da triagem não pôde ser gerado pela IA. Por favor, entre em contato com o suporte da REDE ELLe."

        email_subject = f"Relatório de Triagem REDE ELLe - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"

        email_successfully_sent = send_report_email(email_subject, email_to_send_body)

        if email_successfully_sent:
            st.success("Relatório gerado e enviado para seu e-mail!")
        else:
            st.warning("Relatório gerado, mas houve um problema ao enviar o e-mail. Verifique as configurações de e-mail e os logs.")

        st.session_state.report_filepath, _ = \
            save_report_internally(st.session_state.dados_paciente, relatorio_gerado, email_successfully_sent, email_to_send_body)

        with st.spinner("A IA está elaborando a mensagem final para você..."):
            patient_summary_final = get_final_patient_summary(st.session_state.dados_paciente)
        st.write(f"\n**IA**: {patient_summary_final}")

        st.write("\nSessão de triagem encerrada. Obrigado(a) por sua participação.")
        st.session_state.triagem_flow_state = 'finished'
        st.rerun()

    elif st.session_state.triagem_flow_state == 'finished':
        for chat in st.session_state.chat_history:
            st.write(f"**{chat['speaker']}**: {chat['text']}")
        st.markdown("--- **Sessão Concluída** ---")
        st.info("Para iniciar uma nova sessão, atualize a página no navegador (F5) ou selecione 'Triagem Inicial' no menu.")

# --- Página de Visualizar Relatórios (Acesso Protegido) ---
elif st.session_state.current_page == "Visualizar Relatórios":
    st.header("Relatórios de Triagem da REDE ELLe (Acesso Restrito)")
    st.write("Aqui você pode visualizar e gerenciar todos os relatórios de triagem salvos.")

    reports_list = get_reports_from_db()

    # CORREÇÃO: Inicialização padrão de min_report_id e max_report_id
    # Estes valores só serão usados se reports_list estiver vazia.
    # Se reports_list tiver dados, eles serão sobrescritos abaixo.
    min_report_id = 1
    max_report_id = 1

    if reports_list:
        display_data = []
        for report_item in reports_list:
            report_id, timestamp, patient_name, risk_alert, email_sent = report_item
            display_data.append({
                "ID": report_id,
                "Data/Hora": datetime.datetime.strptime(timestamp, "%Y%m%d_%H%M%S").strftime("%d/%m/%Y %H:%M:%S"),
                "Paciente (Nome-Arquivo)": patient_name,
                "Alerta de Risco": risk_alert,
                "Email Enviado": "Sim" if email_sent == 1 else "Não"
            })

        df = pd.DataFrame(display_data)

        # Atualiza min_report_id e max_report_id com base nos dados reais
        all_report_ids = df['ID'].tolist()
        if all_report_ids: # Confere se a lista de IDs não está vazia antes de pegar min/max
            min_report_id = min(all_report_ids)
            max_report_id = max(all_report_ids)

        st.subheader("Ferramentas de Busca e Filtro")
        col_search, col_risk, col_start_date, col_end_date = st.columns([2, 1, 1, 1])

        with col_search:
            search_query = st.text_input("Buscar por nome do paciente (anonimizado):", key="search_reports")
        with col_risk:
            risk_filter = st.selectbox("Filtrar por Alerta de Risco:", ["Todos", "Sim", "Não"], key="filter_risk")
        with col_start_date:
            default_start_date = datetime.date.today() - datetime.timedelta(days=30)
            if not df.empty:
                min_db_date = pd.to_datetime(df['Data/Hora'], format="%d/%m/%Y %H:%M:%S").min().date()
                if min_db_date < default_start_date:
                    default_start_date = min_db_date
            start_date = st.date_input("Data de Início:", default_start_date, key="start_date_filter")
        with col_end_date:
            end_date = st.date_input("Data de Fim:", datetime.date.today(), key="end_date_filter")

        filtered_df = df.copy()

        if search_query:
            filtered_df = filtered_df[filtered_df["Paciente (Nome-Arquivo)"].str.contains(search_query, case=False, na=False)]
        if risk_filter != "Todos":
            filtered_df = filtered_df[filtered_df["Alerta de Risco"] == risk_filter]

        filtered_df['Data/Hora_dt'] = pd.to_datetime(filtered_df['Data/Hora'], format="%d/%m/%Y %H:%M:%S")
        filtered_df = filtered_df[(filtered_df['Data/Hora_dt'].dt.date >= start_date) & (filtered_df['Data/Hora_dt'].dt.date <= end_date)]

        filtered_df = filtered_df.drop(columns=['Data/Hora_dt'])

        st.subheader("Relatórios Filtrados")
        st.dataframe(filtered_df, use_container_width=True, hide_index=False)

        csv_export = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Exportar Relatórios para CSV",
            data=csv_export,
            file_name="redeelle_relatorios_filtrados.csv",
            mime="text/csv",
            key="download_csv_button"
        )

        st.subheader("Visualizações Gráficas")

        if not filtered_df.empty:
            daily_counts = filtered_df['Data/Hora'].str.split(' ').str[0].value_counts().reset_index()
            daily_counts.columns = ['Data', 'Quantidade']
            daily_counts['Data'] = pd.to_datetime(daily_counts['Data'], format="%d/%m/%Y")
            daily_counts = daily_counts.sort_values('Data')

            chart_daily = alt.Chart(daily_counts).mark_line().encode(
                x=alt.X('Data:T', title='Data'),
                y=alt.Y('Quantidade:Q', title='Quantidade de Relatórios'),
                tooltip=[alt.Tooltip('Data:T', format='%d/%m/%Y'), 'Quantidade:Q']
            ).properties(
                title='Número de Relatórios por Dia'
            ).interactive()
            st.altair_chart(chart_daily, use_container_width=True)

            risk_counts = filtered_df['Alerta de Risco'].value_counts().reset_index()
            risk_counts.columns = ['Alerta', 'Quantidade']

            chart_risk = alt.Chart(risk_counts).mark_arc().encode(
                theta=alt.Theta(field="Quantidade", type="quantitative"),
                color=alt.Color(field="Alerta", type="nominal", title="Alerta de Risco"),
                tooltip=['Alerta', 'Quantidade']
            ).properties(
                title='Distribuição de Alertas de Risco'
            )
            st.altair_chart(chart_risk, use_container_width=True)

        else:
            st.info("Nenhum dado para exibir gráficos com os filtros atuais.")


        st.subheader("Visualizar Detalhes do Relatório Individual")

        if 'report_id_input' not in st.session_state:
            st.session_state.report_id_input = max_report_id

        report_to_view_id = st.number_input(
            "Digite o ID do relatório para visualizar os detalhes:",
            min_value=min_report_id,
            max_value=max_report_id,
            value=st.session_state.report_id_input, # Garante que o valor inicial seja o do estado
            format="%d",
            key="report_id_input"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Relatório Anterior", key="prev_report_button"):
                if report_to_view_id > min_report_id:
                    report_to_view_id -= 1
                    st.session_state.report_id_input = report_to_view_id
                    st.rerun()
        with col2:
            if st.button("Próximo Relatório", key="next_report_button"):
                if report_to_view_id < max_report_id:
                    report_to_view_id += 1
                    st.session_state.report_id_input = report_to_view_id
                    st.rerun()

        if st.button("Ver Detalhes do Relatório", key="view_report_button_final"):
            if report_to_view_id:
                patient_data_full, generated_report_full = get_single_report_from_db(report_to_view_id)
                if patient_data_full:
                    st.markdown(f"**Detalhes do Relatório ID: {report_to_view_id}**")
                    st.markdown("**Dados do Paciente (Triagem Completa):**")
                    for q, r in patient_data_full.items():
                        st.write(f"- **{q}**: {r}")
                    st.markdown("**Relatório de Exame Psíquico (IA):**")
                    st.markdown(generated_report_full)
                else:
                    st.warning("Relatório não encontrado. Verifique o ID.")
            else:
                st.warning("Por favor, insira um ID de relatório para visualizar.")

    else:
        st.info("Nenhum relatório de triagem encontrado até o momento.")

    # --- SEÇÃO DE FEEDBACK INTERNO ---
    # Só exibe a seção de feedback se estiver logado E se houver algum relatório no DB
    if st.session_state.get("logged_in", False) and reports_list: # reports_list agora contem os dados atualizados
        st.markdown("---")
        st.subheader("Fornecer Feedback para um Relatório")

        def clear_feedback_text_area():
            if "feedback_text_area_input" in st.session_state:
                st.session_state.feedback_text_area_input = ""

        if 'feedback_report_id_form_input' not in st.session_state:
            st.session_state.feedback_report_id_form_input = max_report_id

        feedback_report_id = st.number_input(
            "ID do Relatório para Feedback:",
            # A correção do NameError aqui já foi feita pela inicialização padrão acima (min_report_id, max_report_id)
            # e pela atualização desses valores quando reports_list não é vazia.
            min_value=min_report_id, 
            max_value=max_report_id,
            value=st.session_state.feedback_report_id_form_input,
            format="%d",
            key="feedback_report_id_form_input"
        )

        feedback_text_area_content = st.text_area(
            "Seu Feedback/Observação:",
            key="feedback_text_area_input"
        )

        def submit_feedback_and_clear():
            current_feedback_report_id = st.session_state.get('feedback_report_id_form_input')
            current_feedback_text = st.session_state.get('feedback_text_area_input')

            if current_feedback_report_id is not None and current_feedback_text:
                save_feedback_entry(current_feedback_report_id, current_feedback_text)
                st.success(f"Feedback para o relatório ID {current_feedback_report_id} salvo com sucesso!")
                clear_feedback_text_area()
            else:
                st.warning("Por favor, digite um ID de relatório e seu feedback antes de salvar.")

        st.button("Salvar Feedback", on_click=submit_feedback_and_clear, key="save_feedback_button")

        st.subheader(f"Feedbacks Registrados para o Relatório ID {feedback_report_id}")
        current_report_feedbacks = get_feedback_for_report(feedback_report_id)
        if current_report_feedbacks:
            for fb_text, fb_timestamp in current_report_feedbacks:
                formatted_timestamp = datetime.datetime.strptime(fb_timestamp, '%Y%m%d_%H%M%S').strftime('%d/%m/%Y %H:%M:%S')
                st.write(f"- **{formatted_timestamp}**: {fb_text}")
        else:
            st.info("Nenhum feedback registrado para este relatório.")
    elif st.session_state.get("logged_in", False) and not reports_list: # Este é o caso quando está logado mas não há relatórios
        st.info("Faça uma triagem inicial para que os relatórios e a funcionalidade de feedback sejam populares.")
