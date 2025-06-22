import os
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import datetime # Para gerar carimbo de data/hora nos nomes dos arquivos

# Para envio de e-mail
import smtplib
from email.message import EmailMessage

# Adicione estas duas linhas aqui para o SQLite e JSON:
import sqlite3 # Para organizar os dados da triagem
import json    # Para guardar os dados de forma que o computador entenda

# --- Configuração Inicial ---
# Carregar as variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializar o cliente da OpenAI com sua chave de API
# A API Key será lida do .env localmente ou dos Streamlit Secrets em produção
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Configuração da Gaveta de Relatórios (Banco de Dados SQLite) ---
DB_NAME = "redeelle_relatorios.db" # Nome do arquivo do nosso "caderno organizado"

def init_db():
    conn = sqlite3.connect(DB_NAME) # Conecta ou cria o arquivo do caderno
    cursor = conn.cursor()
    # Pede para criar uma "folha" dentro do caderno, se ela não existir
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,         -- Número único para cada relatório
            timestamp TEXT NOT NULL,                      -- Quando foi feito o relatório
            patient_name_for_file TEXT,                   -- Nome anônimo do paciente para o arquivo
            patient_data TEXT NOT NULL,                   -- Todas as perguntas e respostas (como guardamos agora)
            generated_report TEXT NOT NULL,               -- O relatório que a IA gerou
            risk_alert TEXT,                              -- Se teve alerta de risco (suicídio/homicídio)
            email_sent INTEGER                            -- Se o e-mail foi enviado (0 para não, 1 para sim)
        );
    """)
    conn.commit() # Salva as mudanças na folha
    conn.close()  # Fecha o caderno

# Chamamos a função para arrumar o caderno assim que o aplicativo começa
init_db()

# --- Fim da Configuração da Gaveta de Relatórios ---


# Obter credenciais de e-mail do ambiente
SENDER_EMAIL = os.getenv("EMAIL_ADDRESS")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECEIVER_EMAIL = SENDER_EMAIL # Enviamos para o mesmo e-mail, pois é para Carla

# Definir o título da aplicação (aparece na aba do navegador)
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
A quebra de sigilo será feita em caso de falas sobre suicídio e omicídio do escutado.
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
  "Você se sente mais horas na internet ou nas horas livres mais conectado na internet do que com as pessoas?",
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
""" # Removi a "Hipótese Diagnóstica final" daqui para ela ser o ponto final do prompt principal

# --- Funções Auxiliares ---

# Função para COMPILAR o texto completo do relatório (para e-mail, arquivo e DB)
def compile_full_report_text(patient_data, generated_report_content):
    timestamp_for_report = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") # Usa a data/hora atual
    full_report_text = f"--- RELATÓRIO DE TRIAGEM REDE ELLe - {timestamp_for_report} ---\n\n"
    full_report_text += "## Dados Coletados na Triagem:\n"
    for question_key, response_value in patient_data.items():
        full_report_text += f"{question_key}: {response_value}\n"
    full_report_text += "\n---\n\n"
    full_report_text += "## EXAME PSÍQUICO com devolutiva Psicanalítica (Gerado pela IA):\n"
    if generated_report_content:
        full_report_text += generated_report_content
    else:
        full_report_text += "Relatório da IA não pôde ser gerado devido a erro.\n"
    full_report_text += "\n---\n"
    full_report_text += "Sessão finalizada com sucesso.\n"
    return full_report_text

def checar_risco_imediato(texto):
  """
  Função simples para verificar palavras-chave de risco.
  IMPORTANTE: Isso é uma verificação básica e não substitui a avaliação humana.
  """
  texto_lower = texto.lower()
  if "suicídio" in texto_lower or "homicídio" in texto_lower or "matar" in texto_lower:
    return True
  return False

def get_emotional_reflection(feeling_text):
  """
  Função para gerar uma reflexão emocional acolhedora usando a API da OpenAI para o sentimento inicial.
  """
  try:
    response = client.chat.completions.create(
      model="gpt-3.5-turbo", # Modelo mais econômico para reflexões curtas
      messages=[
        {"role": "system", "content": "Você é um assistente de IA com escuta ampliada e acolhimento simbólico. Ao receber o sentimento inicial de um participante, ofereça uma breve reflexão (1-2 frases, máximo 20 palavras) que valide essa expressão, convidando-o sutilmente a um espaço de aprofundamento, sem ser repetitivo ou superficial."},
        {"role": "user", "content": f"O participante disse: '{feeling_text}'. Como você o acolheria?"}
      ],
      temperature=0.8,
      max_tokens=60
    )
    return response.choices[0].message.content
  except Exception as e:
    st.warning(f"Não foi possível obter uma reflexão inicial da IA: {e}")
    return f"Compreendo... É importante reconhecer como você se sente {feeling_text}." # Fallback

def get_triagem_reflection(patient_answer):
  """
  Função para gerar uma reflexão acolhedora a cada resposta do paciente durante a triagem.
  """
  try:
    response = client.chat.completions.create(
      model="gpt-3.5-turbo", # Modelo mais econômico para reflexões curtas
      messages=[
        {"role": "system", "content": "Você é um assistente de IA da REDE ELLe, praticando a escuta ampliada. Após cada resposta do participante, ofereça uma breve e humana validação (1-2 frases, máximo 25 palavras) que reconheça a importância do que foi compartilhado, incentivando a continuidade da narrativa, sem emitir julgamentos."},
        {"role": "user", "content": f"O participante acabou de responder: '{patient_answer}'. Como você responderia de forma empática antes de fazer a próxima pergunta?"}
      ],
      temperature=0.7,
      max_tokens=70
    )
    return response.choices[0].message.content
  except Exception as e:
    st.warning(f"Não foi possível obter uma reflexão para a triagem: {e}")
    return "Entendo. Agradeço por compartilhar." # Fallback


def get_final_patient_summary(dados_paciente_temp):
  """
  Gera um resumo acolhedor para o paciente no final da sessão, destacando a coragem e os próximos passos.
  """
  summary_data = []
  # Pegar os dados principais que o paciente trouxe
  for q_key, p_response in dados_paciente_temp.items():
    if "IA: " not in q_key: # Evita pegar as falas da IA no histórico
      summary_data.append(f"{q_key.replace('Pergunta', 'Em sua resposta sobre ').replace(':', '')}: {p_response}")
  
  summary_text = "\n".join(summary_data)

  try:
    response = client.chat.completions.create(
      model="gpt-3.5-turbo", # Modelo mais econômico para o resumo final do paciente
      messages=[
        {"role": "system", "content": "Você é a voz da REDE ELLe, oferecendo um espaço de escuta ampliada e simbólica. Ao final da triagem, elabore uma mensagem final (entre 90 e 180 palavras) para o participante. Esta mensagem deve humanamente reconhecer a profundidade e a coragem da partilha, refletir brevemente sobre a jornada iniciada, e reiterar que seu caminho de elaboração está sendo cuidadosamente acolhido. Garanta que a mensagem finalize com a clara informação de que as vivências serão encaminhadas à Psicanalista Clínica Carla Viviane Guedes Ferreira (REDE ELLe), que em breve fará contato para os próximos passos da jornada. Use linguagem que ressoe com os princípios da psicanálise de forma acessível, sem termos técnicos ou diagnósticos."},
        {"role": "user", "content": f"O participante compartilhou as seguintes informações: {summary_text}. Por favor, crie a mensagem final para ele."}
      ],
      temperature=0.7,
      max_tokens=200
    )
    return response.choices[0].message.content
  except Exception as e:
    st.warning(f"Não foi possível gerar o resumo final para o paciente: {e}")
    return ("Agradeço imensamente pela sua disponibilidade em compartilhar suas vivências conosco. Sua sessão de escuta inicial foi concluída com sucesso e suas informações serão analisadas com o cuidado e a ética que lhe são devidos. Nossa equipe entrará em contato em breve para os próximos passos.")


def gerar_relatorio_gpt(dados_paciente_temp):
  """
  Função para gerar o relatório do exame psíquico usando a API da OpenAI.
  Agora inclui perspectivas teóricas.
  """
  historico_triagem = "Registro da Triagem:\n"
  for pergunta, resposta in dados_paciente_temp.items():
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
        model="gpt-4o", # Usamos o modelo GPT-4o para o relatório, pois é mais complexo
        messages=[
          {"role": "system", "content": "Você é uma IA assistente psicanalítica, auxiliar da Psicanalista Clínica Carla Viviane Guedes Ferreira (REDE ELLe). Seu objetivo é gerar relatórios de triagem detalhados e analíticos para uso profissional."},
          {"role": "user", "content": prompt_para_relatorio}
        ],
        temperature=0.7, # Um pouco mais de criatividade para as perspectivas teóricas e sugestões
        max_tokens=2200 # Aumentei o limite de tokens para comportar as novas seções detalhadas
      )
    return resposta_gpt.choices[0].message.content
  except Exception as e:
    st.error(f"Ocorreu um erro ao gerar o relatório com a IA: {e}")
    st.warning("Por favor, verifique se sua chave de API está correta e se você tem créditos na OpenAI.")
    return None

def save_report_internally(patient_data, generated_report, email_sent_status, compiled_report_text):
    """
    Função atualizada:
    1. Salva o report_text (já formatado) em um arquivo de texto.
    2. Insere tudo também no nosso 'caderno digital' (banco de dados SQLite).
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") # Pega a data e hora atual
    
    patient_name_for_file = "PacienteAnonimo" # Nome padrão para o arquivo
    q1_data = patient_data.get("Pergunta 1: Qual seu nome, idade, whatsapp e cidade?", "")
    if q1_data: # Tenta extrair o nome da primeira pergunta
        name_parts = q1_data.split(',')[0].strip()
        if name_parts:
            # Limpa o nome para que possa ser usado no nome do arquivo
            patient_name_for_file = "".join(c for c in name_parts if c.isalnum() or c == ' ').strip().replace(" ", "_").replace("__", "_")
            if not patient_name_for_file:
                patient_name_for_file = "PacienteAnonimo"

    filename_full = f"relatorio_{patient_name_for_file}_{timestamp}.txt" # Nome completo do arquivo de texto
    
    reports_dir = "relatorios_triagem" # Pasta onde os arquivos são salvos
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir) # Cria a pasta se não existir

    filepath = os.path.join(reports_dir, filename_full) # Caminho completo para o arquivo de texto

    # Salva o conteúdo no arquivo de texto
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(compiled_report_text) # Use o texto já compilado
    
    # --- NOVIDADE: GUARDAR NO CADERNO DIGITAL (SQLite) ---
    conn = sqlite3.connect(DB_NAME) # Conecta ao caderno digital
    cursor = conn.cursor()

    # Transforma as perguntas/respostas para um formato que o caderno digital entenda
    patient_data_json = json.dumps(patient_data, ensure_ascii=False) 

    # Vê se teve alerta de risco
    risk_alert_status = "Sim" if patient_data.get("ALERTA_RISCO_IMEDIATO") == "Sim" else "Não"
    
    # Adiciona uma nova linha com todos os detalhes no caderno digital
    cursor.execute("""
        INSERT INTO reports (timestamp, patient_name_for_file, patient_data, generated_report, risk_alert, email_sent)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (
        timestamp,
        patient_name_for_file,
        patient_data_json,
        generated_report, # Gera o raw generated GPT report (sem os metadados do cabeçalho) no DB
        risk_alert_status,
        1 if email_sent_status else 0 # Marca 1 se o e-mail foi enviado, 0 se não
    ))
    conn.commit() # Salva as mudanças no caderno
    conn.close()  # Fecha o caderno
    # --- FIM DA NOVIDADE ---

    return filepath, compiled_report_text # Devolve o caminho do arquivo e o conteúdo para o e-mail

def send_report_email(subject, body, filepath=None):
  """
  Envia o relatório por e-mail para o RECEIVER_EMAIL.
  """
  if not SENDER_EMAIL or not SENDER_PASSWORD:
    st.error("Credenciais de e-mail não configuradas no arquivo .env ou Secrets do Streamlit. Envio de e-mail falhou.") 
    return False

  msg = EmailMessage()
  msg['Subject'] = subject
  msg['From'] = SENDER_EMAIL
  msg['To'] = RECEIVER_EMAIL
  msg.set_content(body)

  # Opcional: Anexar o arquivo se for fornecido o caminho
  if filepath and os.path.exists(filepath):
    # Determine o tipo MIME com base na extensão do arquivo
    import mimetypes
    mimestart = mimetypes.guess_type(filepath)[0]
    if mimestart is not None:
      maintype, subtype = mimestart.split('/')
    else:
      maintype = 'application'
      subtype = 'octet-stream' # Tipo genérico caso não consiga identificar

    with open(filepath, 'rb') as f:
      file_data = f.read()
      file_name = os.path.basename(filepath)
    msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)

  try:
    # Usar 465 com SSL para Gmail
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp: 
      # smtp.set_debuglevel(1) # Descomente para depurar o envio de e-mail no terminal
      smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
      smtp.send_message(msg)
    return True
  except smtplib.SMTPAuthenticationError as e:
    st.error(f"Erro de autenticação SMTP: Suas credenciais de e-mail estão incorretas ou você precisa de uma senha de aplicativo para o Gmail. Erro: {e}")
    return False
  except Exception as e:
    st.error(f"Erro ao enviar o e-mail: {e}")
    return False

# --- Lógica do Streamlit App ---

st.title("Psicanálise Digital com Escuta Ampliada – REDE ELLe")
st.subheader("Seu espaço de acolhimento e escuta inicial")

# Inicializar o estado da sessão (CORREÇÃO DE st.session_session_state para st.session_state)
if 'current_step' not in st.session_state:
  st.session_state.current_step = 'consent' # Estado inicial: pedir consentimento
  st.session_state.dados_paciente = {} # Armazena as respostas da triagem
  st.session_state.current_question_index = 0 # Índice da pergunta atual
  st.session_state.chat_history = [] # Para exibir a conversa
  st.session_state.report_filepath = None # Para armazenar o caminho do relatório salvo
  st.session_state.report_content_for_email = None # Para armazenar o conteúdo do relatório para email

# --- Etapa de Consentimento ---
if st.session_state.current_step == 'consent':
  st.markdown("### Por favor, leia o Termo de Consentimento Informado abaixo:")
  st.markdown(TERMO_CONSENTIMENTO)
  if st.button("Eu concordo e quero iniciar a triagem"):
    st.session_state.current_step = 'initial_greeting'
    st.session_state.chat_history.append({"speaker": "IA", "text": "Oi. Aqui é seu espaço de escuta sem julgamento e com acolhimento. Como se sente hoje?"})
    st.rerun()

# --- Etapa de Saudação Inicial ---
elif st.session_state.current_step == 'initial_greeting':
  for chat in st.session_state.chat_history:
    st.write(f"**{chat['speaker']}**: {chat['text']}")

  user_input = st.text_input("Paciente:", key="initial_feeling_input")
  if user_input:
    st.session_state.dados_paciente['sentimento_inicial'] = user_input
    st.session_state.chat_history.append({"speaker": "Paciente", "text": user_input})
    
    # Gerar reflexão mais elaborada
    reflection_text = get_emotional_reflection(user_input)
    st.session_state.chat_history.append({"speaker": "IA", "text": reflection_text})
    
    st.session_state.chat_history.append({"speaker": "IA", "text": "Aqui vamos iniciar o recode, para entender melhor o que se passa com você, então farei algumas perguntas, e sinta-se livre para responder quanto e como quiser."})
    st.session_state.current_step = 'triagem_questions'
    st.rerun()

# --- Etapa de Perguntas da Triagem ---
elif st.session_state.current_step == 'triagem_questions':
  # Exibi o histórico do chat
  for chat in st.session_state.chat_history:
    st.write(f"**{chat['speaker']}**: {chat['text']}")

  if st.session_state.current_question_index <= len(TRIAGEM_PERGUNTAS): # Aumentei o <= para pegar a última pergunta antes do resumo
    # Verifica se já passamos por todas as perguntas e vamos para o resumo
    if st.session_state.current_question_index == len(TRIAGEM_PERGUNTAS):
      # Todas as perguntas foram respondidas, agora exibir o "Agradeço e aguarde"
      st.session_state.chat_history.append({"speaker": "IA", "text": "Agradeço suas respostas. As informações coletadas são muito importantes."})
      st.session_state.chat_history.append({"speaker": "IA", "text": "Agora estou preparando um resumo e um exame psíquico preliminar para a Psicanalista Carla Viviane Guedes Ferreira."})
      st.session_state.chat_history.append({"speaker": "IA", "text": "Por favor, aguarde alguns instantes..."})
      st.session_state.current_step = 'generate_report'
      st.rerun()
    else: # Ainda há perguntas para fazer
      current_question = TRIAGEM_PERGUNTAS[st.session_state.current_question_index]
      
      # Exibe a pergunta atual da IA
      st.write(f"**IA**: {current_question}")
      user_response = st.text_input("Paciente:", key=f"question_input_{st.session_state.current_question_index}")

      if user_response:
        st.session_state.chat_history.append({"speaker": "Paciente", "text": user_response})
        
        # Armazenar a pergunta e a resposta
        st.session_state.dados_paciente[f"Pergunta {st.session_state.current_question_index+1}: {current_question}"] = user_response

        # Checar risco imediato
        if checar_risco_imediato(user_response):
          st.warning("!!! ATENÇÃO !!! Foi detectada uma fala relacionada a risco de suicídio ou homicídio.")
          st.warning("Lembre-se do item 4 do Termo de Consentimento: 'A quebra de sigilo será feita em caso de falas sobre suicídio e homicídio do escutado.' É crucial que você procure ajuda profissional imediata.")
          st.session_state.dados_paciente["ALERTA_RISCO_IMEDIATO"] = "Sim" # Flag para o relatório

        # Gerar reflexão para a resposta específica da triagem (se não for a última pergunta)
        if st.session_state.current_question_index < len(TRIAGEM_PERGUNTAS) -1: # Para não gerar reflexão depois da última pergunta
          reflection_triagem = get_triagem_reflection(user_response)
          st.session_state.chat_history.append({"speaker": "IA", "text": reflection_triagem})

        st.session_state.current_question_index += 1
        st.rerun()
  else: # Esta parte não deveria ser alcançada com a lógica atual ajustada acima, mas mantida para segurança.
    st.session_state.chat_history.append({"speaker": "IA", "text": "Agradeço suas respostas. As informações coletadas são muito importantes."})
    st.session_state.chat_history.append({"speaker": "IA", "text": "Agora estou preparando um resumo e um exame psíquico preliminar para a Psicanalista Carla Viviane Guedes Ferreira."})
    st.session_state.chat_history.append({"speaker": "IA", "text": "Por favor, aguarde alguns instantes..."})
    st.session_state.current_step = 'generate_report'
    st.rerun()


# --- Etapa de Geração e Salvamento do Relatório ---
elif st.session_state.current_step == 'generate_report':
  # Exibi o histórico do chat
  for chat in st.session_state.chat_history:
    st.write(f"**{chat['speaker']}**: {chat['text']}")

  # Geração do relatório (chamada à API)
  relatorio_gerado = gerar_relatorio_gpt(st.session_state.dados_paciente)
    
  if relatorio_gerado:
      # Primeiro: Compila o texto completo do relatório para o e-mail e para salvar no arquivo/DB
      # Isso garante que st.session_state.report_content_for_email NÃO seja None
      st.session_state.report_content_for_email = compile_full_report_text(st.session_state.dados_paciente, relatorio_gerado)
      
      # Tentar enviar o e-mail
      email_subject = f"Relatório de Triagem REDE ELLe - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
      email_body = st.session_state.report_content_for_email # Agora o corpo do e-mail está preenchido
      
      email_successfully_sent = send_report_email(email_subject, email_body) # <--- ESSA LINHA NÃO VAI MAIS BUGA AQUI!
      
      if email_successfully_sent: 
          st.success("Relatório gerado e enviado para seu e-mail!")
      else:
          st.warning("Relatório gerado, mas houve um problema ao enviar o e-mail. Verifique as configurações de e-mail e os logs.")

      # Salvar o relatório nos arquivos e no DB (passando o texto já gerado e o status do e-mail)
      st.session_state.report_filepath, _ = \
          save_report_internally(st.session_state.dados_paciente, relatorio_gerado, email_successfully_sent, st.session_state.report_content_for_email)

      # Mensagem final para o paciente (agora gerada pela IA)
      with st.spinner("A IA está elaborando a mensagem final para você..."):
          patient_summary_final = get_final_patient_summary(st.session_state.dados_paciente)
      st.write(f"\n**IA**: {patient_summary_final}")
      
  else:
      st.error("Desculpe, não foi possível gerar o relatório completo neste momento. Por favor, tente novamente mais tarde.")
  
  st.write("\nSessão de triagem encerrada. Obrigado(a) por sua participação.")
  st.session_state.current_step = 'finished' # Marca como concluído
  st.rerun()

# --- Etapa Final (para que a barra de input não apareça depois de terminar) ---
elif st.session_state.current_step == 'finished':
  for chat in st.session_state.chat_history:
    st.write(f"**{chat['speaker']}**: {chat['text']}")
  st.markdown("--- **Sessão Concluída** ---")
  st.info("Para iniciar uma nova sessão, atualize a página no navegador (F5).")
