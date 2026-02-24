import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import re
import gspread
import json
from datetime import datetime
import pytz

# --- CONFIGURAÇÃO DA IA E SEGURANÇA ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    modelos_validos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    if modelos_validos:
        model = genai.GenerativeModel(modelos_validos[0])
    else:
        st.error("Nenhum modelo compatível encontrado para esta chave.")
except Exception as e:
    st.error("⚠️ Configure a chave GOOGLE_API_KEY nos Secrets do Streamlit.")

# --- CONEXÃO COM O GOOGLE SHEETS (MÁQUINA DE LEADS) ---
google_sheets_connected = False
try:
    # Puxa o "crachá" do cofre de forma segura
    credenciais_dict = json.loads(st.secrets["gcp_json"])
    gc = gspread.service_account_from_dict(credenciais_dict)
    
    # Abre a planilha pelo nome exato que você criou
    planilha = gc.open("Dados - Curadoria TellMe")
    aba_leads = planilha.worksheet("Leads")
    aba_uso = planilha.worksheet("Uso")
    google_sheets_connected = True
except Exception as e:
    # Se falhar a conexão, o app continua funcionando silenciosamente, só não salva os dados.
    pass

def pegar_data_hora():
    fuso_brasil = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso_brasil).strftime("%d/%m/%Y %H:%M:%S")

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Curadoria TellMe", page_icon="🧡", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Dosis:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Dosis', sans-serif; }
    .stApp { background-color: #ffffff; color: #1a2b48; }
    .stButton>button { 
        background-color: #f37021; color: white; border-radius: 20px; 
        border: none; padding: 12px 25px; font-weight: bold; width: 100%; font-size: 16px;
    }
    .stTextArea textarea { border: 1px solid #1a2b48; border-radius: 10px; }
    .nota-destaque { font-size: 36px; font-weight: bold; color: #f37021; text-align: center; margin-bottom: 5px; }
    .nota-mensagem { font-size: 18px; text-align: center; margin-bottom: 25px; color: #1a2b48; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGO GLOBAL ---
try:
    st.image("Logo.png", width=180)
except Exception:
    st.warning("⚠️ Imagem não encontrada. Verifique se o arquivo se chama exatamente 'Logo.png'.")

# --- FLUXO DA APLICAÇÃO ---
if 'setup_pronto' not in st.session_state:
    
    st.title("Crie mensagens que encantam e conectam as famílias 🧡")
    st.write("Para que nossa Inteligência Artificial ajude você a transformar comunicados comuns em verdadeiros elos de parceria, precisamos entender o estilo único da sua escola.")
    
    with st.form("setup"):
        
        st.markdown("### Seus Dados")
        escola = st.text_input("Nome da Escola", placeholder="Ex: Colégio TellMe Prime")
        email = st.text_input("Seu E-mail Corporativo", placeholder="diretor@suaescola.com.br")
        
        st.markdown("### Como é a voz da sua escola?")
        st.markdown("*Esta é a chave para a personalização. Ao definir o perfil da sua instituição, você calibra a nossa IA para criar comunicados autênticos e alinhados aos seus valores, poupando o seu tempo de revisão.*")
        
        formal = st.slider("Formalidade (0 = Descontraída e Casual | 5 = Clássica e Institucional)", 0, 5, 2)
        afeto = st.slider("Afetividade (0 = Focada na Informação Direta | 5 = Altamente Acolhedora e Emocional)", 0, 5, 4)
        objetivo = st.slider("Objetividade (0 = Rica em Contexto e Detalhes | 5 = Rápida e Resumida em Tópicos)", 0, 5, 3)
        pedagogia = st.slider("Nível Pedagógico (0 = Linguagem Leiga e Traduzida | 5 = Termos Técnicos e Científicos)", 0, 5, 2)
        
        if st.form_submit_button("Preparar meu Consultor TellMe"):
            if escola and email:
                st.session_state.setup_pronto = True
                st.session_state.escola = escola
                st.session_state.email = email
                st.session_state.formal = formal
                st.session_state.afeto = afeto
                st.session_state.objetivo = objetivo
                st.session_state.pedagogia = pedagogia
                
                # --- SALVA O LEAD NA PLANILHA ---
                if google_sheets_connected:
                    try:
                        aba_leads.append_row([pegar_data_hora(), escola, email])
                    except Exception:
                        pass
                
                st.rerun()
            else:
                st.warning("Por favor, preencha o Nome da Escola e o seu E-mail para continuarmos.")

else:
    st.title(f"Curadoria TellMe: {st.session_state.escola}")
    st.caption(f"Usuário: {st.session_state.email}")
    
    col1, col2 = st.columns(2)
    with col1:
        objetivo_msg = st.selectbox("Objetivo da Mensagem", ["Inspirar", "Engajar", "Tranquilizar", "Informar"])
    with col2:
        segmento = st.selectbox("Segmento Alvo", ["Educação Infantil", "Ensino Fundamental I", "Ensino Fundamental II", "Ensino Médio"])
    
    mensagem_bruta = st.text_area("Cole aqui o rascunho da sua comunicação:", height=180)

    if st.button("Ativar Curadoria TellMe"):
        if mensagem_bruta:
            with st.spinner('A IA TellMe está calibrando sua mensagem para encantar as famílias...'):
                
                prompt_sistema = f"""
                Aja como um Consultor Especialista em Comunicação Escolar da plataforma TellMe. 
                Sua missão é ajudar a escola a criar mensagens que encantam e conectam as famílias.
                
                ESTILO DE COMUNICAÇÃO DA ESCOLA (Escala 0 a 5):
                - Formalidade: {st.session_state.formal}/5
                - Afetividade: {st.session_state.afeto}/5
                - Objetividade: {st.session_state.objetivo}/5
                - Nível Pedagógico/Técnico: {st.session_state.pedagogia}/5

                TAREFA:
                Avalie a mensagem abaixo para o segmento {segmento} com o objetivo de {objetivo_msg}.
                Dê notas de 1 a 5 para estes critérios: Clareza, Contexto, Intencionalidade, Sinergia e Simplicidade.

                FORMATO DE RESPOSTA OBRIGATÓRIO:
                NOTAS: [nota_clareza],[nota_contexto],[nota_intencionalidade],[nota_sinergia],[nota_simplicidade]
                FEEDBACK: [Um parágrafo de consultoria explicando os acertos e erros em relação ao estilo da escola]
                PERGUNTA: [Uma pergunta prática para o pai fazer ao filho hoje, no tom exato do estilo da escola]

                Mensagem para análise: {mensagem_bruta}
                """
                
                try:
                    response = model.generate_content(prompt_sistema)
                    ai_res = response.text
                    
                    notas_match = re.search(r"NOTAS:\s*([\d,]+)", ai_res)
                    feedback_match = re.search(r"FEEDBACK:\s*(.*)", ai_res)
                    pergunta_match = re.search(r"PERGUNTA:\s*(.*)", ai_res)
                    
                    if notas_match:
                        notas = [int(n.strip()) for n in notas_match.group(1).split(',')]
                        soma_notas = sum(notas)
                        nota_final = round((soma_notas / 25) * 10)
                        
                        # --- SALVA O USO NA PLANILHA ---
                        if google_sheets_connected:
                            try:
                                aba_uso.append_row([pegar_data_hora(), st.session_state.email, segmento, objetivo_msg, nota_final])
                            except Exception:
                                pass

                        if nota_final <= 3:
                            msg_padrao = "Sua mensagem é burocrática. Vamos humanizá-la e mostrar valor."
                        elif nota_final <= 5:
                            msg_padrao = "Faltou contexto para aproximar os pais da escola."
                        elif nota_final <= 7:
                            msg_padrao = "Boa! Mas um pequeno ajuste transforma o recado em parceria."
                        elif nota_final <= 9:
                            msg_padrao = "Excelente! Empática e convida a família a participar."
                        else:
                            msg_padrao = "Padrão Ouro! A verdadeira 'Conversa que Educa'."

                        st.markdown(f"<div class='nota-destaque'>Sua nota é {nota_final}/10</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='nota-mensagem'><em>{msg_padrao}</em></div>", unsafe_allow_html=True)
                        st.divider()
                        
                        df_radar = pd.DataFrame(dict(r=notas, theta=['Clareza', 'Contexto', 'Intencionalidade', 'Sinergia', 'Simplicidade']))
                        fig = px.line_polar(df_radar, r='r', theta='theta', line_close=True, range_r=[0,5])
                        fig.update_traces(fill='toself', fillcolor='rgba(243, 112, 33, 0.4)', line_color='#f37021')
                        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=False, margin=dict(t=20, b=20))
                        st.plotly_chart(fig)
                        
                        st.markdown("### 💡 Diagnóstico da Curadoria")
                        st.info(feedback_match.group(1) if feedback_match else "Análise concluída.")
                        
                        st.markdown("### 🧡 Momento 'Conversa que Educa'")
                        st.markdown("*Envie a sugestão abaixo para fortalecer o elo família-escola.*")
                        st.success(pergunta_match.group(1) if pergunta_match else "Gere uma nova pergunta.")
                        
                        st.divider()
                        st.markdown("### 📘 Saiba como criar mensagens que encantam")
                        st.markdown("*Entenda os 5 pilares que a nossa Curadoria TellMe utiliza para avaliar e transformar a comunicação da sua escola:*")
                        st.markdown("""
                        * **🎯 Clareza:** A mensagem vai direto ao ponto? Os pais precisam entender exatamente o que está acontecendo logo na primeira leitura, sem ambiguidades ou ruídos.
                        * **🌍 Contexto:** O comunicado explica o "porquê" das coisas? Dar contexto transforma um simples aviso burocrático em uma história na qual a família se sente parte.
                        * **🚀 Intencionalidade:** Qual é o objetivo real do envio? Toda mensagem deve ter um propósito claro sobre o que queremos que a família sinta, reflita ou faça após a leitura.
                        * **🤝 Sinergia:** O texto aproxima a escola de casa? Uma comunicação sinérgica cria pontes, mostrando que pais e educadores estão no mesmo time pelo desenvolvimento do aluno.
                        * **🍃 Simplicidade:** O vocabulário é acessível e humano? Evitar termos excessivamente técnicos e frases complexas garante que a mensagem seja acolhedora para todos.
                        """)
                        
                except Exception as e:
                    st.error(f"Erro ao processar análise. A IA está configurada corretamente? Detalhe: {e}")
        else:
            st.warning("Por favor, cole o rascunho da sua mensagem para ativar a análise.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🔄 Sair e Ajustar Estilo"):
        st.session_state.clear()
        st.rerun()