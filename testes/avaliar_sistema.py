# avaliar_sistema.py
"""
Script de Avaliação Experimental do UNESPedia
Compara LLMs (Gemini, Deepseek, Claude) e Vector Stores (ChromaDB, FAISS)
"""

import time
import json
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
import pypdf
import io

# Importar módulos do projeto
import yaml
from llm_handler import gerar_resposta_com_llm
from rag_processor import dividir_texto_em_chunks, buscar_contexto_relevante
from vector_store_factory import get_vector_store
import secrets_manager

def carregar_config():
    """Carrega configuração sem Streamlit."""
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


# =============================================================================
# CONFIGURAÇÃO DO EXPERIMENTO
# =============================================================================

# PDFs para teste (coloque na pasta do projeto)
PDFS_TESTE = [
    "Security_Mitigation_Fails.pdf",
    "ML_Attacks_Metrics.pdf", 
    "DL_Attacks_Types.pdf"
]

# Perguntas de teste (carregar do Excel)
EXCEL_PERGUNTAS = "Perguntas.xlsx"

# LLMs a testar
LLM_PROVIDERS = ["Gemini", "Deepseek", "Claude"]

# Vector Stores a testar
VECTOR_STORES = ["ChromaDB", "FAISS"]

# Configuração de geração
CONFIG_GERACAO = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048
}


# =============================================================================
# FUNÇÕES DE AVALIAÇÃO
# =============================================================================

def carregar_perguntas():
    """Carrega perguntas do Excel."""
    try:
        df = pd.read_excel(EXCEL_PERGUNTAS)
        
        # Adaptar nomes de colunas
        if 'Pergunta (Query)' in df.columns:
            df['pergunta'] = df['Pergunta (Query)']
        if 'Resposta Ouro (GT Answer)' in df.columns:
            df['resposta_esperada'] = df['Resposta Ouro (GT Answer)']
        
        # Garantir que tem as colunas necessárias
        if 'pergunta' not in df.columns:
            print("⚠️  Coluna 'pergunta' não encontrada, usando primeira coluna")
            df['pergunta'] = df.iloc[:, 0]
        
        if 'resposta_esperada' not in df.columns:
            df['resposta_esperada'] = ""
        
        return df[['pergunta', 'resposta_esperada']].to_dict('records')
        
    except Exception as e:
        print(f"❌ Erro ao carregar perguntas: {e}")
        # Fallback para perguntas hardcoded
        return [
            {
                "pergunta": "Qual foi a Taxa de Falso Negativo (FNR) para DNS Spoofing?",
                "resposta_esperada": "0.40"
            },
            {
                "pergunta": "Quantas features foram reduzidas usando PCA no estudo de Regressão Logística?",
                "resposta_esperada": "75 para 12"
            },
            {
                "pergunta": "Qual foi o Recall da LSTM no estudo de DDoS?",
                "resposta_esperada": "98.5%"
            }
        ]


def processar_pdfs(vector_store_config):
    """Processa PDFs e retorna tempo de indexação."""
    print(f"\n📄 Processando {len(PDFS_TESTE)} PDFs...")
    
    start_time = time.time()
    
    # Criar vector store
    vs = get_vector_store(vector_store_config)
    
    # Processar cada PDF com chunk_size reduzido
    lista_chunks = []
    lista_metadados = []
    
    for pdf_path in PDFS_TESTE:
        if not os.path.exists(pdf_path):
            print(f"⚠️  Arquivo não encontrado: {pdf_path}")
            continue
            
        try:
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()
                reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
                
                print(f"  📄 {pdf_path}: {len(reader.pages)} páginas")
                
                texto = "".join(
                    p.extract_text() or "" 
                    for p in reader.pages
                )
                
                if not texto.strip():
                    print(f"  ⚠️  Nenhum texto extraído de {pdf_path}")
                    continue
                
                print(f"  📝 Texto extraído: {len(texto)} caracteres")
                
                # FORÇAR CHUNKING SIMPLES para textos curtos
                # Se o texto todo cabe em um chunk, usar ele inteiro
                if len(texto) < 1000:
                    chunks = [texto]
                    metadados = [{"fonte": pdf_path, "page": 1, "section": "Documento completo"}]
                    print(f"  ✂️  Texto curto - usando como 1 chunk")
                else:
                    chunks, metadados = dividir_texto_em_chunks(texto, pdf_path)
                    print(f"  ✂️  Gerados {len(chunks)} chunks")
                
                lista_chunks.extend(chunks)
                lista_metadados.extend(metadados)
        except Exception as e:
            print(f"❌ Erro ao processar {pdf_path}: {e}")
    
    # Adicionar ao vector store
    if lista_chunks:
        vs.adicionar(lista_chunks, lista_metadados)
    
    tempo_indexacao = time.time() - start_time
    
    print(f"✅ Indexados {len(lista_chunks)} chunks em {tempo_indexacao:.2f}s")
    
    return vs, tempo_indexacao, len(lista_chunks)


def avaliar_citacoes(resposta):
    """Avalia qualidade das citações na resposta."""
    # Conta citações no formato (Fonte, p. X, sec. Y) ou com placeholders
    import re
    
    # Padrões:
    # 1. (arquivo.pdf, p. 1, sec. 1) - normal
    # 2. (arquivo.pdf, p. {page}, sec. {section}) - com placeholders
    # 3. (arquivo.pdf) - só arquivo
    citacoes = re.findall(r'\([^)]*\.pdf[^)]*\)', resposta)
    
    return {
        "num_citacoes": len(citacoes),
        "tem_citacoes": len(citacoes) > 0,
        "citacoes_encontradas": citacoes[:5]  # Primeiras 5
    }


def avaliar_resposta_llm(provider, api_key, model_config, vector_store, pergunta, nomes_ficheiros):
    """Avalia uma resposta de um LLM."""
    print(f"\n🤖 Testando {provider}...")
    
    # Tempo de busca no vector store
    start_busca = time.time()
    contexto = buscar_contexto_relevante(vector_store, pergunta, nomes_ficheiros)
    tempo_busca = time.time() - start_busca
    
    # Tempo de geração da resposta
    start_geracao = time.time()
    resposta = gerar_resposta_com_llm(
        provider_name=provider,
        api_key=api_key,
        model_config=model_config,
        contexto=contexto,
        pergunta=pergunta,
        historico_chat=[],
        nomes_ficheiros=nomes_ficheiros,
        config_geracao=CONFIG_GERACAO
    )
    tempo_geracao = time.time() - start_geracao
    
    # Avaliar citações
    qualidade_citacoes = avaliar_citacoes(resposta)
    
    return {
        "provider": provider,
        "pergunta": pergunta,
        "resposta": resposta,
        "tempo_busca_ms": tempo_busca * 1000,
        "tempo_geracao_ms": tempo_geracao * 1000,
        "tempo_total_ms": (tempo_busca + tempo_geracao) * 1000,
        "tamanho_resposta": len(resposta),
        **qualidade_citacoes
    }


def estimar_custo(provider, num_tokens_entrada, num_tokens_saida):
    """Estima custo aproximado por consulta."""
    # Preços aproximados por 1M tokens (valores de referência)
    precos = {
        "Gemini": {"entrada": 0.075, "saida": 0.30},  # Flash
        "Claude": {"entrada": 3.00, "saida": 15.00},  # Sonnet
        "Deepseek": {"entrada": 0.27, "saida": 1.10},
        "OpenAI": {"entrada": 3.00, "saida": 15.00}   # GPT-4
    }
    
    if provider not in precos:
        return 0.0
    
    custo_entrada = (num_tokens_entrada / 1_000_000) * precos[provider]["entrada"]
    custo_saida = (num_tokens_saida / 1_000_000) * precos[provider]["saida"]
    
    return custo_entrada + custo_saida


# =============================================================================
# EXPERIMENTO PRINCIPAL
# =============================================================================

def executar_experimento():
    """Executa o experimento completo."""
    print("="*70)
    print("🧪 AVALIAÇÃO EXPERIMENTAL - UNESPedia")
    print("="*70)
    
    config = carregar_config()
    providers_config = config['llm_providers']
    vector_stores_config = config['vector_stores']
    
    # Carregar perguntas
    perguntas = carregar_perguntas()
    print(f"\n📋 {len(perguntas)} perguntas carregadas")
    
    resultados = []
    
    # ==== EXPERIMENTO 1: Comparar Vector Stores ====
    print("\n" + "="*70)
    print("📊 EXPERIMENTO 1: Comparação de Vector Stores")
    print("="*70)
    
    metricas_vs = {}
    
    for vs_name in VECTOR_STORES:
        print(f"\n🗄️  Testando {vs_name}...")
        
        vs_config = vector_stores_config[vs_name]
        vs, tempo_idx, num_chunks = processar_pdfs(vs_config)
        
        metricas_vs[vs_name] = {
            "tempo_indexacao_s": tempo_idx,
            "num_chunks": num_chunks,
            "tempo_por_chunk_ms": (tempo_idx / num_chunks) * 1000 if num_chunks > 0 else 0
        }
    
    # ==== EXPERIMENTO 2: Comparar LLMs ====
    print("\n" + "="*70)
    print("🤖 EXPERIMENTO 2: Comparação de LLMs")
    print("="*70)
    
    # Usar ChromaDB como padrão para testes de LLM
    vs_padrao_config = vector_stores_config["ChromaDB"]
    vs_padrao, _, _ = processar_pdfs(vs_padrao_config)
    
    for provider in LLM_PROVIDERS:
        api_key = secrets_manager.get_api_key(provider)
        
        if not api_key or "SUA_CHAVE" in str(api_key):
            print(f"⚠️  Pulando {provider} - sem chave API configurada")
            continue
        
        print(f"\n{'='*70}")
        print(f"🤖 Testando {provider.upper()}")
        print(f"{'='*70}")
        
        model_config = providers_config[provider]
        
        for i, pergunta_item in enumerate(perguntas, 1):
            pergunta = pergunta_item['pergunta']
            
            print(f"  📝 Pergunta {i}/{len(perguntas)}: {pergunta[:50]}...")
            
            try:
                resultado = avaliar_resposta_llm(
                    provider=provider,
                    api_key=api_key,
                    model_config=model_config,
                    vector_store=vs_padrao,
                    pergunta=pergunta,
                    nomes_ficheiros=PDFS_TESTE
                )
                
                # Estimar custo
                tokens_entrada = len(pergunta.split()) * 1.3  # Aproximação
                tokens_saida = len(resultado['resposta'].split()) * 1.3
                resultado['custo_estimado_usd'] = estimar_custo(
                    provider, tokens_entrada, tokens_saida
                )
                
                resultados.append(resultado)
                print(f"  ✅ Tempo: {resultado['tempo_total_ms']:.0f}ms | Citações: {resultado['num_citacoes']}")
                
            except Exception as e:
                print(f"  ❌ Erro: {str(e)[:60]}...")
                continue
    
    # ==== SALVAR RESULTADOS ====
    print("\n" + "="*70)
    print("💾 Salvando Resultados...")
    print("="*70)
    
    if not resultados:
        print("⚠️  Nenhum resultado de LLM coletado!")
        print("   Verifique se as chaves API estão configuradas corretamente.")
        return {}, metricas_vs
    
    # Criar diretório de resultados
    Path("resultados_experimento").mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Salvar métricas de Vector Stores
    df_vs = pd.DataFrame.from_dict(metricas_vs, orient='index')
    df_vs.to_csv(f"resultados_experimento/metricas_vectorstores_{timestamp}.csv")
    print(f"✅ Métricas de Vector Stores salvas")
    
    # 2. Salvar métricas de LLMs
    df_llm = pd.DataFrame(resultados)
    df_llm.to_csv(f"resultados_experimento/metricas_llms_{timestamp}.csv", index=False)
    print(f"✅ Métricas de LLMs salvas")
    
    # 3. Criar resumo estatístico
    resumo = df_llm.groupby('provider').agg({
        'tempo_total_ms': ['mean', 'std', 'min', 'max'],
        'num_citacoes': ['mean', 'sum'],
        'tem_citacoes': 'sum',
        'custo_estimado_usd': 'sum'
    }).round(3)
    
    resumo.to_csv(f"resultados_experimento/resumo_estatistico_{timestamp}.csv")
    print(f"✅ Resumo estatístico salvo")
    
    # 4. Salvar respostas completas (para análise qualitativa)
    with open(f"resultados_experimento/respostas_completas_{timestamp}.json", 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"✅ Respostas completas salvas")
    
    # ==== MOSTRAR RESUMO ====
    print("\n" + "="*70)
    print("📈 RESUMO DOS RESULTADOS")
    print("="*70)
    
    print("\n🗄️  VECTOR STORES:")
    print(df_vs.to_string())
    
    print("\n\n🤖 LLMs (Resumo Estatístico):")
    print(resumo.to_string())
    
    print("\n" + "="*70)
    print("✅ Experimento concluído!")
    print(f"📁 Resultados salvos em: resultados_experimento/")
    print("="*70)
    
    return resultados, metricas_vs


# =============================================================================
# EXECUÇÃO
# =============================================================================

if __name__ == "__main__":
    try:
        resultados, metricas_vs = executar_experimento()
    except Exception as e:
        print(f"\n❌ Erro durante experimento: {e}")
        import traceback
        traceback.print_exc()