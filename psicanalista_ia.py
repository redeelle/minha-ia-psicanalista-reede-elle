import os
from openai import OpenAI
from dotenv import load_dotenv

# Carregar as variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializar o cliente da OpenAI com sua chave de API
# A chave será carregada do arquivo .env se estiver configurado corretamente
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- 1º - TERMO DE CONSENTIMENTO INFORMADO ---
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
A empresa responsável pela tecnologia da IA, não possui acesso direto aos conteúdos gerados nesta experiência e não se responsabiliza pelo uso clínico realizado por terceiros. O conteúdo das respostas é baseado em algoritmos de predição de linguagem natural, não se tratando de orientação psicológica ou médica.
6. Direito de retirada:
Você pode encerrar sua participação a qualquer momento, sem qualquer tipo de prejuízo, penalidade ou justificativa. O vínculo simbólico e subjetivo será respeitado mesmo em caso de silêncio ou ausência.
7. Registro e privacidade de dados:
Com sua autorização expressa, o conteúdo da interação poderá ser gravado de forma anônima para fins de pesquisa, análise simbólica ou desenvolvimento institucional da REDE ELLe. Nenhum dado pessoal ou identificável será divulgado. Os dados tratados obedecerão às disposições da Lei Geral de Proteção de Dados (LGPD) – Lei nº 13.709/2018, a qual pode ser consultada na íntegra no site oficial do Governo Federal:
https://www.gov.br/lgpd
"""

# --- 2º - TRIAGEM ---
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

# --- 3º - EXAME PSÍQUICO (Instruções para o GPT) ---
EXAME_PSIQUICO_INSTRUCOES = """
Como foi o comportamento do paciente?
Atitude para com a IA triadora: Cooperativo? Resistente? Indiferente?
Orientação: Auto-identificatória? Corporal? Temporal? Espacial? Orientado em relação a patologia?

Quais foram as tuas observações?
Me fale sobre a memória do paciente?
Me fale sobre a inteligência do paciente?
Qual a sensopercepção: Normal? Alucinação?
Pensamento: Acelerado? Retardado? Fuga? Bloqueio? Prolixo? Repetição?
Linguagem: Disartria (má articulação)? Afasias, verbigeração (repetição de palavras)? Parafasia (emprego inapropriado de palavras com sentidos parecidos)? Neologismo? Mussitação (voz murmurada em som baixo)? Logorréia (fluxo incessante e incoercível de palavras)? Para-respostas (responde a uma indagação com algo que não tem nada a ver com oque foi perguntado)?

Como é a afetividade do paciente?
Humor do paciente: normal? exaltado? baixa-de-humor? Quebra súbita de tonalidade de humor durante a entrevista?
Consciência do estado mental?
Hipótese Diagnóstica final:
"""

def checar_risco_imediato(texto):
    """
    Função simples para verificar palavras-chave de risco.
    IMPORTANTE: Isso é uma verificação básica e não substitui a avaliação humana.
    """
    texto_lower = texto.lower()
    if "suicídio" in texto_lower or "homicídio" in texto_lower or "matar" in texto_lower:
        return True
    return False

def main():
    print("--- Bem-vindo(a) à Psicanálise Digital com Escuta Ampliada – REDE ELLe ---")

    # --- FASE 1: TERMO DE CONSENTIMENTO ---
    print("\nPor favor, leia o Termo de Consentimento Informado abaixo:")
    print(TERMO_CONSENTIMENTO)
    consentimento = input("\nPara continuar, digite 'Eu concordo': ").strip().lower()

    if consentimento != "eu concordo":
        print("Você optou por não participar. A sessão será encerrada.")
        return # Termina o programa

    print("\nObrigado(a) por sua concordância. Vamos iniciar a triagem.\n")

    # Armazena as respostas do paciente
    dados_paciente = {}

    # --- FASE 2: TRIAGEM ---
    print("IA: Oi. Aqui é seu espaço de escuta sem julgamento e com acolhimento. Como se sente hoje?")
    sentimento_inicial = input("Paciente: ")
    dados_paciente['sentimento_inicial'] = sentimento_inicial

    # Simples reflexão baseada no sentimento inicial (poderia ser uma chamada ao GPT para ser mais sofisticado)
    print(f"IA: Posso imaginar que você se sente {sentimento_inicial}...\n")
    print("IA: Aqui vamos iniciar o recode, para entender melhor o que se passa com você, então farei algumas perguntas, e sinta-se livre para responder quanto e como quiser.\n")

    # Loop pelas perguntas da triagem
    for i, pergunta in enumerate(TRIAGEM_PERGUNTAS):
        print(f"IA: {pergunta}")
        resposta = input("Paciente: ")
        
        # Armazenar a pergunta e a resposta para o relatório final
        dados_paciente[f"Pergunta {i+1}: {pergunta}"] = resposta

        # Checagem de risco imediato após cada resposta
        if checar_risco_imediato(resposta):
            print("\n!!! ATENÇÃO !!!")
            print("IA: Foi detectada uma fala relacionada a risco de suicídio ou homicídio.")
            print("IA: Lembre-se do item 4 do Termo de Consentimento: 'A quebra de sigilo será feita em caso de falas sobre suicídio e homicídio do escutado.'")
            print("IA: É crucial que você procure ajuda profissional imediata.")
            # Você pode adicionar lógica aqui para notificar Carla, encerrar a sessão, etc.
            dados_paciente["ALERTA_RISCO_IMEDIATO"] = "Sim" # Flag para o relatório

    print("\nIA: Agradeço suas respostas. As informações coletadas são muito importantes.")
    print("IA: Agora estou preparando um resumo e um exame psíquico preliminar para a Psicanalista Carla Viviane Guedes Ferreira, como parte da sua triagem e análise inicial.")
    print("IA: Por favor, aguarde alguns instantes...")

    # --- FASE 3: GERAÇÃO DO RELATÓRIO DO EXAME PSÍQUICO ---
    # Convertendo os dados do paciente para um formato legível para o GPT
    historico_triagem = "Registro da Triagem:\n"
    for pergunta, resposta in dados_paciente.items():
        historico_triagem += f"- {pergunta}: {resposta}\n"

    # Criando o prompt final para o GPT gerar o relatório
    prompt_para_relatorio = f"""
    Você é uma Inteligência Artificial auxiliar da Psicanalista Clínica Carla Viviane Guedes Ferreira (REDE ELLe).
    Sua tarefa é analisar as informações fornecidas por um paciente durante uma triagem inicial e gerar um 'EXAME PSÍQUICO com devolutiva Psicanalítica' conforme a estrutura fornecida.
    É fundamental que você preencha CADA seção do relatório com base nas respostas do paciente. Faça inferências e observações pertinentes onde for possível e necessário, mas deixe claro se uma informação é uma inferência ou se está ausente.

    ## Informações do Paciente e Respostas da Triagem:
    {historico_triagem}

    ## Estrutura do EXAME PSÍQUICO a ser preenchido:

    {EXAME_PSIQUICO_INSTRUCOES}

    Por favor, gere o relatório preenchendo as seções acima com base nas informações fornecidas. Seja conciso, mas completo e analítico.
    """

    try:
        # Chamada à API da OpenAI para gerar o relatório
        # Usamos o modelo 'gpt-4o' conforme especificado no termo de consentimento
        resposta_gpt = client.chat.completions.create(
            model="gpt-4o", # Modelo especificado no TERMO DE CONSENTIMENTO
            messages=[
                {"role": "system", "content": "Você é uma IA assistente psicanalítica, auxiliar da Psicanalista Clínica Carla Viviane Guedes Ferreira (REDE ELLe). Seu objetivo é gerar relatórios de triagem."},
                {"role": "user", "content": prompt_para_relatorio}
            ],
            temperature=0.7, # Controla a criatividade da IA (0.0 a 1.0). 0.7 é um bom equilíbrio para conteúdo analítico.
            max_tokens=1500 # Limite de tamanho para a resposta do relatório
        )

        relatorio_gerado = resposta_gpt.choices[0].message.content

        print("\n--- RELATÓRIO DO EXAME PSÍQUICO PARA CARLA VIVIANE GUEDES FERREIRA ---")
        print(relatorio_gerado)
        print("--- FIM DO RELATÓRIO ---")
        print("\nIA: Este relatório foi gerado e está pronto para análise da profissional responsável.")

    except Exception as e:
        print(f"\nOcorreu um erro ao gerar o relatório com a IA: {e}")
        print("Por favor, verifique se sua chave de API está correta e se você tem créditos na OpenAI.")
        print("Você também pode verificar sua conexão com a internet.")

    print("\nSessão de triagem encerrada. Obrigado(a) por sua participação.")
    
# Garante que a função 'main' seja executada quando o script for iniciado
if __name__ == "__main__":
    main()