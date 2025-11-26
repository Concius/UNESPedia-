# researcher_profile.py

import streamlit as st
from llm_handler import gerar_resposta_com_llm
from collections import Counter
import re

def gerar_perfil_pesquisador(nome_pesquisador, lista_metadados, 
                             vector_store, provider_name, api_key, 
                             model_config, config_geracao):
    """
    Gera um perfil científico consolidado de um pesquisador.
    
    Args:
        nome_pesquisador: Nome do pesquisador
        lista_metadados: Lista de dicionários com metadados de TODOS os artigos
        vector_store: Vector store para buscar contexto adicional
        provider_name: Nome do provedor LLM
        api_key: Chave API
        model_config: Configuração do modelo
        config_geracao: Parâmetros de geração
    
    Returns:
        str: Perfil formatado em Markdown
    """
    # Importação local para evitar circular imports
    try:
        from metadata_extractor import filtrar_artigos_por_autor
    except ImportError:
        from metadata_extractor_v2 import filtrar_artigos_por_autor
    
    # Filtrar apenas os artigos do pesquisador
    artigos_filtrados = filtrar_artigos_por_autor(
        lista_metadados, 
        nome_pesquisador, 
        threshold=0.7
    )
    
    if not artigos_filtrados:
        return f"❌ Nenhum artigo encontrado para o pesquisador '{nome_pesquisador}'."
    
    # Construir contexto estruturado dos artigos
    contexto_estruturado = construir_contexto_artigos(
        nome_pesquisador, 
        artigos_filtrados, 
        vector_store
    )
    
    # Extrair palavras-chave por frequência (ajuda o LLM)
    keywords_sugeridas = extrair_palavras_chave_simples(artigos_filtrados)
    keywords_str = ", ".join(keywords_sugeridas) if keywords_sugeridas else "N/A"
    
    # Prompt especializado para geração de perfil
    prompt_perfil = f"""
Você é um analista científico especializado em criar perfis de pesquisadores.

**IMPORTANTE:** Você está analisando EXCLUSIVAMENTE a produção científica de **{nome_pesquisador}**.
NÃO confunda com outros autores que aparecem como coautores nos artigos.

**CONTEXTO:**
{contexto_estruturado}

**PALAVRAS-CHAVE DETECTADAS POR FREQUÊNCIA:**
{keywords_str}

**TAREFA:**
Gere um perfil científico completo de **{nome_pesquisador}** contendo:

## 1. Resumo da Linha de Pesquisa (200-300 palavras)
- Principais áreas de atuação
- Foco metodológico
- Abordagens preferenciais
- Evolução temporal dos tópicos (se identificável)

## 2. Principais Contribuições Científicas
Liste 3-5 contribuições mais relevantes identificadas nos artigos.
Para cada contribuição:
- Descrição breve (1-2 linhas)
- Artigo(s) correspondente(s)

## 3. Palavras-chave da Pesquisa
Identifique 10-15 palavras-chave/termos técnicos mais frequentes e relevantes.
Use as palavras-chave detectadas acima como base, mas refine e complete a lista.
Ordene por relevância/frequência.
Formato: palavra-chave1, palavra-chave2, palavra-chave3, ...

## 4. Colaboradores Frequentes
Liste até 5 coautores que aparecem em múltiplos artigos (se houver).

## 5. Análise Temporal (se aplicável)
- Como a pesquisa evoluiu ao longo dos anos?
- Mudanças de foco ou novas direções identificáveis?

**FORMATO DE SAÍDA:**
Use markdown com seções claras (## para títulos).
Seja objetivo e baseie-se APENAS no conteúdo fornecido.
Não invente informações.

**LEMBRE-SE:** Este perfil é sobre **{nome_pesquisador}** especificamente, não sobre os tópicos gerais dos artigos.
"""

    # Gerar perfil usando LLM
    try:
        perfil = gerar_resposta_com_llm(
            provider_name=provider_name,
            api_key=api_key,
            model_config=model_config,
            contexto=contexto_estruturado,
            pergunta=prompt_perfil,
            historico_chat=[],  # Sem histórico, é geração standalone
            nomes_ficheiros=[a['fonte'] for a in artigos_filtrados],
            config_geracao=config_geracao
        )
        return perfil
    except Exception as e:
        # Fallback: perfil básico com keywords extraídas
        st.warning(f"⚠️ Erro ao gerar perfil com LLM: {e}")
        st.info("📊 Gerando perfil básico com análise estatística...")
        
        perfil_fallback = f"""# Perfil Científico de {nome_pesquisador}

**⚠️ Nota:** Este perfil foi gerado automaticamente por análise estatística devido a erro na geração via LLM.

## Estatísticas Básicas
- **Total de artigos:** {len(artigos_filtrados)}
- **Anos de publicação:** {min([a.get('ano', 9999) for a in artigos_filtrados if a.get('ano')])} - {max([a.get('ano', 0) for a in artigos_filtrados if a.get('ano')])}

## Palavras-chave Detectadas (por frequência)
{', '.join(keywords_sugeridas) if keywords_sugeridas else "Nenhuma palavra-chave detectada"}

## Artigos Analisados
"""
        for i, artigo in enumerate(artigos_filtrados, 1):
            perfil_fallback += f"\n{i}. **{artigo['titulo']}** ({artigo.get('ano', 'N/A')})\n"
        
        return perfil_fallback


def construir_contexto_artigos(nome_pesquisador, artigos_filtrados, vector_store):
    """
    Constrói contexto estruturado dos artigos para o LLM.
    """
    contexto = f"# Análise da Produção Científica de {nome_pesquisador}\n\n"
    contexto += f"**Total de artigos analisados:** {len(artigos_filtrados)}\n\n"
    
    # Ordenar por ano (mais recente primeiro)
    artigos_ordenados = sorted(
        artigos_filtrados, 
        key=lambda x: x.get('ano', 0) or 0, 
        reverse=True
    )
    
    for idx, artigo in enumerate(artigos_ordenados, 1):
        contexto += f"\n## Artigo {idx}: {artigo['titulo']}\n"
        contexto += f"- **Autores:** {', '.join(artigo['autores'][:5])}"
        if len(artigo['autores']) > 5:
            contexto += f" (e outros {len(artigo['autores']) - 5})"
        contexto += "\n"
        
        if artigo.get('ano'):
            contexto += f"- **Ano:** {artigo['ano']}\n"
        
        # Verificar posição do pesquisador
        try:
            posicao = next(
                i for i, autor in enumerate(artigo['autores']) 
                if nome_pesquisador.lower() in autor.lower()
            )
            if posicao == 0:
                contexto += f"- **Posição do pesquisador:** Primeiro autor\n"
            else:
                contexto += f"- **Posição do pesquisador:** {posicao + 1}º autor\n"
        except StopIteration:
            contexto += f"- **Posição do pesquisador:** Coautor\n"
        
        # Abstract
        if artigo.get('abstract'):
            contexto += f"\n**Abstract:**\n{artigo['abstract'][:800]}\n"
        
        # Buscar contexto adicional do vector store
        if vector_store:
            try:
                resultados = vector_store.buscar(
                    query_texts=f"main contribution methodology results {artigo['titulo'][:50]}",
                    n_results=2,
                    where={"fonte": artigo['fonte']}
                )
                
                if resultados and resultados.get('documents') and resultados['documents'][0]:
                    contexto += f"\n**Trechos relevantes do artigo:**\n"
                    for doc in resultados['documents'][0][:2]:
                        contexto += f"- {doc[:200]}...\n"
            except Exception:
                pass  # Ignora erros na busca do vector store
        
        contexto += "\n" + "="*50 + "\n"
    
    return contexto


def extrair_palavras_chave_simples(artigos_filtrados):
    """
    Extração simples de palavras-chave por frequência (fallback).
    Usa caso o LLM falhe.
    """
    # Coletar todo o texto dos abstracts
    texto_completo = " ".join([
        artigo.get('abstract', '') for artigo in artigos_filtrados
    ])
    
    # Limpar e tokenizar
    texto_limpo = re.sub(r'[^\w\s]', ' ', texto_completo.lower())
    palavras = texto_limpo.split()
    
    # Remover stopwords básicas
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'be',
        'this', 'that', 'these', 'those', 'we', 'our', 'their', 'it', 'its',
        'de', 'da', 'do', 'das', 'dos', 'em', 'para', 'com', 'por', 'uma',
        'um', 'os', 'as', 'na', 'no', 'que', 'se', 'é', 'ou', 'foi', 'são',
        'can', 'using', 'used', 'based', 'paper', 'study', 'research', 'work',
        'approach', 'method', 'propose', 'show', 'result', 'found', 'abstract',
        'introduction', 'conclusion', 'keywords', 'references'
    }
    
    palavras_filtradas = [
        p for p in palavras 
        if len(p) > 3 and p not in stopwords
    ]
    
    # Contar frequências
    contador = Counter(palavras_filtradas)
    
    # Retornar top 15
    return [palavra for palavra, _ in contador.most_common(15)]