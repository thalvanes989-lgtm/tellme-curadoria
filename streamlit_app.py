import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import re

# --- CONFIGURAÇÃO DA IA ---
GOOGLE_API_KEY = "AIzaSyA-ZvZfYO0Z9OUYRW6lXf9crgDH8kZ_0KM"

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    modelos_validos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    if modelos_validos:
        model = genai.GenerativeModel(modelos_validos[0])
    else:
        st.error("Nenhum modelo compatível encontrado para esta chave.")
except Exception as e:
    st.error(f"Erro na configuração da API: {e}")

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

# --- LOGO GLOBAL (Alinhada à Esquerda) ---
try:
    st.image("Logo.png", width=180)
except Exception:
    st.warning("⚠️ Imagem não encontrada. Verifique se o arquivo na barra lateral se chama exatamente 'Logo.png' (tudo minúsculo).")

# --- FLUXO DA APLICAÇÃO ---
if 'setup_pronto' not in st.session_state:
    
    st.title("Crie mensagens que encantam e conectam as famílias 🧡")
    st.write("Para que nossa Inteligência Artificial ajude você a transformar comunicados comuns em verdadeiros elos de parceria, precisamos entender o estilo único da sua escola. Ajuste as réguas abaixo para nos ensinar como vocês gostam de conversar.")
    
    with st.form("setup"):
        
        # --- NOVO BLOCO DO NOME DA ESCOLA (Maior e com destaque) ---
        st.markdown("### Nome da Escola")
        escola = st.text_input("escola_input", placeholder="Ex: Colégio Ipê Amarelo", label_visibility="collapsed")
        
        # --- NOVO BLOCO DA VOZ DA ESCOLA (Com a Copy Estratégica) ---
        st.markdown("### Como é a voz da sua escola?")
        st.markdown("*Esta é a chave para a personalização. Ao definir o perfil da sua instituição, você calibra a nossa IA para criar comunicados autênticos e alinhados aos seus valores, poupando o seu tempo de revisão.*")
        
        formal = st.slider("Formalidade (0 = Descontraída e Casual | 5 = Clássica e Institucional)", 0, 5, 2)
        afeto = st.slider("Afetividade (0 = Focada na Informação Direta | 5 = Altamente Acolhedora e Emocional)", 0, 5, 4)
        objetivo = st.slider("Objetividade (0 = Rica em Contexto e Detalhes | 5 = Rápida e Resumida em Tópicos)", 0, 5, 3)
        pedagogia = st.slider("Nível Pedagógico (0 = Linguagem Leiga e Traduzida | 5 = Termos Técnicos e Científicos)", 0, 5, 2)
        
        if st.form_submit_button("Preparar meu Consultor TellMe"):
            if escola:
                st.session_state.setup_pronto = True
                st.session_state.escola = escola
                st.session_state.formal = formal
                st.session_state.afeto = afeto
                st.session_state.objetivo = objetivo
                st.session_state.pedagogia = pedagogia
                st.rerun()
            else:
                st.warning("Por favor, informe o nome da escola para continuarmos.")

else:
    st.title(f"Curadoria TellMe: {st.session_state.escola}")
    
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
                Sua missão é ajudar a escola a criar mensagens que encantam e conectam as famílias, transformando recados burocráticos em verdadeiras parcerias.
                
                ESTILO DE COMUNICAÇÃO DA ESCOLA (Escala 0 a 5):
                - Formalidade: {st.session_state.formal}/5
                - Afetividade: {st.session_state.afeto}/5
                - Objetividade: {st.session_state.objetivo}/5
                - Nível Pedagógico/Técnico: {st.session_state.pedagogia}/5
                *Regra de Ouro: O seu conselho e a pergunta gerada DEVEM respeitar estritamente este estilo para não descaracterizar a escola.*

                TAREFA:
                Avalie a mensagem abaixo para o segmento {segmento} com o objetivo de {objetivo_msg}.
                Dê notas de 1 a 5 para estes critérios: Clareza, Contexto, Intencionalidade, Sinergia e Simplicidade.

                FORMATO DE RESPOSTA OBRIGATÓRIO:
                NOTAS: [nota_clareza],[nota_contexto],[nota_intencionalidade],[nota_sinergia],[nota_simplicidade]
                FEEDBACK: [Um parágrafo de consultoria focado em engajamento, explicando onde o texto acertou ou errou em relação ao estilo da escola]
                PERGUNTA: [Uma pergunta prática para o pai fazer ao filho hoje, escrita no tom exato do estilo da escola]

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
                        
                        if nota_final <= 3:
                            msg_padrao = "Sua mensagem está funcionando apenas como um recado burocrático. Vamos humanizá-la e mostrar o real valor pedagógico para as famílias."
                        elif nota_final <= 5:
                            msg_padrao = "Você entregou a informação básica, mas perdeu a chance de engajar. Faltou contexto para aproximar os pais da escola."
                        elif nota_final <= 7:
                            msg_padrao = "Boa comunicação! A informação está clara, mas um pequeno ajuste na intencionalidade pode transformar esse recado em uma verdadeira parceria."
                        elif nota_final <= 9:
                            msg_padrao = "Excelente! Sua mensagem é empática e gera valor. Ela convida a família a participar ativamente da jornada do aluno."
                        else:
                            msg_padrao = "Padrão Ouro! Esta é a verdadeira 'Conversa que Educa'. Você dominou a comunicação e usou a TellMe com maestria para encantar as famílias!"

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
                        st.markdown("*Nosso foco é ajudar sua escola a produzir mensagens que ressoem com os pais e inspirem ações em casa. Envie a sugestão abaixo junto com o seu comunicado para fortalecer o elo família-escola e reforçar o aprendizado.*")
                        st.success(pergunta_match.group(1) if pergunta_match else "Gere uma nova pergunta.")
                        
                except Exception as e:
                    st.error(f"Erro ao processar análise: {e}")
        else:
            st.warning("Por favor, cole o rascunho da sua mensagem para ativar a análise.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🔄 Ajustar Estilo da Escola"):
        del st.session_state.setup_pronto
        st.rerun()