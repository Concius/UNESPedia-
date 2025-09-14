# llm_handler.py



import streamlit as st
import google.generativeai as genai
from config_loader import carregar_config

# Carrega a configuração no início do módulo
config = carregar_config()
llm_config = config['llm_defaults']

def gerar_resposta_com_llm(contexto, pergunta, api_key, nomes_ficheiros, historico_chat, debug_mode=False, 
                           temperature=llm_config['temperature'], 
                           top_p=llm_config['top_p'], 
                           top_k=llm_config['top_k'], 
                           max_output_tokens=llm_config['max_output_tokens']):
    """Envia o prompt para o Gemini com parâmetros configuráveis."""
    try:
        genai.configure(api_key=api_key)
        
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_output_tokens,
        )
        
        #Verificação do que está sendo enviado para a API
        st.caption(f"🔧 **Config enviado para API:** T={temperature}, P={top_p}, K={top_k}, Max={max_output_tokens}")
        
        model = genai.GenerativeModel('gemini-1.5-flash', generation_config=generation_config)
        
        if debug_mode:
            st.write("📁 DEBUG: Arquivos que foram processados:")
            for i, nome in enumerate(nomes_ficheiros):
                st.write(f"  {i+1}. {nome}")
        
        # Formata o histórico do chat
        historico_formatado = "\\n".join([f"{msg['role']}: {msg['content']}" for msg in historico_chat])
        
        if debug_mode:
            st.write(f"💬 DEBUG: Histórico tem {len(historico_chat)} mensagens")
            st.write(f"🎛️ DEBUG: Parâmetros do LLM - Temperature: {temperature}, Top-p: {top_p}, Top-k: {top_k}, Max tokens: {max_output_tokens}")

        prompt = f"""
        **Instruções:** Você é um assistente de pesquisa. Responda à "Última pergunta do usuário" baseando-se no "Contexto" e no "Histórico da Conversa".
        Os ficheiros carregados pelo usuário são: {', '.join(nomes_ficheiros)}.

        **Histórico da Conversa:**
        {historico_formatado}

        **Contexto extraído dos documentos (use para basear a sua resposta):**
        ---
        {contexto}
        ---

        **Última pergunta do usuário:** {pergunta}

        **Sua Resposta:**
        """
        
        if debug_mode:
            with st.expander("🤖 DEBUG: Prompt enviado para o LLM"):
                st.text(prompt)
                st.write(f"📏 Tamanho total do prompt: {len(prompt)} caracteres")
        
        resposta = model.generate_content(prompt)
        
        # NOVO: Após gerar a resposta, mostrar metadados se disponível
        if hasattr(resposta, 'usage_metadata'):
            st.caption(f"📊 **Usage API:** {resposta.usage_metadata}")
        
        if debug_mode:
            st.write(f"✅ DEBUG: LLM respondeu com {len(resposta.text)} caracteres")
            # Tentar mostrar mais detalhes da resposta
            if hasattr(resposta, 'candidates'):
                st.write(f"🔍 DEBUG: Número de candidatos: {len(resposta.candidates)}")
        
        return resposta.text
    except Exception as e:
        st.error(f"Erro ao comunicar com a API do Gemini: {e}")
        return "Desculpe, ocorreu um erro ao tentar gerar a resposta."