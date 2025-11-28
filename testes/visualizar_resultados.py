# visualizar_resultados.py
"""
Script para visualizar os resultados do experimento
Gera gráficos comparativos para os slides
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

# Configurar estilo
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 11

def encontrar_arquivos_mais_recentes():
    """Encontra os arquivos CSV mais recentes."""
    resultado_dir = Path("resultados_experimento")
    
    if not resultado_dir.exists():
        print("❌ Diretório 'resultados_experimento' não encontrado!")
        print("Execute primeiro: python avaliar_sistema.py")
        sys.exit(1)
    
    csvs = list(resultado_dir.glob("*.csv"))
    
    if not csvs:
        print("❌ Nenhum arquivo CSV encontrado!")
        sys.exit(1)
    
    # Encontrar mais recentes
    metricas_vs = sorted(resultado_dir.glob("metricas_vectorstores_*.csv"))[-1]
    metricas_llm = sorted(resultado_dir.glob("metricas_llms_*.csv"))[-1]
    
    return metricas_vs, metricas_llm


def criar_graficos():
    """Cria todos os gráficos."""
    print("📊 Gerando gráficos...")
    
    metricas_vs_path, metricas_llm_path = encontrar_arquivos_mais_recentes()
    
    # Carregar dados
    df_vs = pd.read_csv(metricas_vs_path, index_col=0)
    df_llm = pd.read_csv(metricas_llm_path)
    
    # Criar diretório para gráficos
    graficos_dir = Path("resultados_experimento/graficos")
    graficos_dir.mkdir(exist_ok=True)
    
    # ========== GRÁFICO 1: Tempo de Indexação (Vector Stores) ==========
    plt.figure(figsize=(8, 6))
    ax = df_vs['tempo_indexacao_s'].plot(kind='bar', color=['#1f77b4', '#ff7f0e'])
    plt.title('Tempo de Indexação - Vector Stores', fontsize=14, fontweight='bold')
    plt.ylabel('Tempo (segundos)')
    plt.xlabel('Vector Store')
    plt.xticks(rotation=0)
    plt.grid(axis='y', alpha=0.3)
    
    # Adicionar valores no topo das barras
    for i, v in enumerate(df_vs['tempo_indexacao_s']):
        ax.text(i, v + 0.1, f'{v:.2f}s', ha='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(graficos_dir / '1_tempo_indexacao.png', dpi=300, bbox_inches='tight')
    print("✅ Gráfico 1: Tempo de Indexação")
    plt.close()
    
    # ========== GRÁFICO 2: Tempo de Resposta por LLM ==========
    plt.figure(figsize=(10, 6))
    resumo_tempo = df_llm.groupby('provider')['tempo_total_ms'].mean().sort_values()
    ax = resumo_tempo.plot(kind='barh', color=['#2ca02c', '#d62728', '#9467bd'])
    plt.title('Tempo Médio de Resposta por LLM', fontsize=14, fontweight='bold')
    plt.xlabel('Tempo (ms)')
    plt.ylabel('Provedor LLM')
    plt.grid(axis='x', alpha=0.3)
    
    # Adicionar valores
    for i, v in enumerate(resumo_tempo):
        ax.text(v + 50, i, f'{v:.0f}ms', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(graficos_dir / '2_tempo_resposta_llm.png', dpi=300, bbox_inches='tight')
    print("✅ Gráfico 2: Tempo de Resposta")
    plt.close()
    
    # ========== GRÁFICO 3: Qualidade das Citações ==========
    plt.figure(figsize=(10, 6))
    citacoes = df_llm.groupby('provider')['num_citacoes'].mean().sort_values(ascending=False)
    ax = citacoes.plot(kind='bar', color=['#8c564b', '#e377c2', '#7f7f7f'])
    plt.title('Número Médio de Citações por LLM', fontsize=14, fontweight='bold')
    plt.ylabel('Número de Citações')
    plt.xlabel('Provedor LLM')
    plt.xticks(rotation=45)
    plt.grid(axis='y', alpha=0.3)
    
    # Adicionar valores
    for i, v in enumerate(citacoes):
        ax.text(i, v + 0.1, f'{v:.1f}', ha='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(graficos_dir / '3_qualidade_citacoes.png', dpi=300, bbox_inches='tight')
    print("✅ Gráfico 3: Qualidade das Citações")
    plt.close()
    
    # ========== GRÁFICO 4: Custo Estimado por LLM ==========
    plt.figure(figsize=(10, 6))
    custos = df_llm.groupby('provider')['custo_estimado_usd'].sum().sort_values()
    ax = custos.plot(kind='barh', color=['#bcbd22', '#17becf', '#ff9896'])
    plt.title('Custo Total Estimado por LLM', fontsize=14, fontweight='bold')
    plt.xlabel('Custo (USD)')
    plt.ylabel('Provedor LLM')
    plt.grid(axis='x', alpha=0.3)
    
    # Adicionar valores
    for i, v in enumerate(custos):
        ax.text(v + 0.0001, i, f'${v:.4f}', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(graficos_dir / '4_custo_estimado.png', dpi=300, bbox_inches='tight')
    print("✅ Gráfico 4: Custo Estimado")
    plt.close()
    
    # ========== GRÁFICO 5: Comparação Geral (Radar) ==========
    # Normalizar métricas para 0-1
    metricas_normalizadas = df_llm.groupby('provider').agg({
        'tempo_total_ms': 'mean',
        'num_citacoes': 'mean',
        'custo_estimado_usd': 'sum'
    })
    
    # Inverter tempo (menor é melhor)
    metricas_normalizadas['velocidade'] = 1 - (
        metricas_normalizadas['tempo_total_ms'] / metricas_normalizadas['tempo_total_ms'].max()
    )
    
    # Normalizar citações
    metricas_normalizadas['qualidade'] = (
        metricas_normalizadas['num_citacoes'] / metricas_normalizadas['num_citacoes'].max()
    )
    
    # Inverter custo (menor é melhor)
    metricas_normalizadas['custo_beneficio'] = 1 - (
        metricas_normalizadas['custo_estimado_usd'] / metricas_normalizadas['custo_estimado_usd'].max()
    )
    
    # Criar tabela comparativa
    plt.figure(figsize=(12, 4))
    tabela_dados = metricas_normalizadas[['velocidade', 'qualidade', 'custo_beneficio']].round(3)
    tabela_dados.columns = ['Velocidade\n(0-1)', 'Qualidade\n(0-1)', 'Custo-Benefício\n(0-1)']
    
    ax = plt.subplot(111, frame_on=False)
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    
    table = pd.plotting.table(ax, tabela_dados, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 2)
    
    # Colorir células
    for (i, j), cell in table.get_celld().items():
        if i == 0:
            cell.set_facecolor('#4CAF50')
            cell.set_text_props(weight='bold', color='white')
        else:
            val = tabela_dados.iloc[i-1, j]
            if val > 0.7:
                cell.set_facecolor('#90EE90')
            elif val > 0.4:
                cell.set_facecolor('#FFE4B5')
            else:
                cell.set_facecolor('#FFB6C1')
    
    plt.title('Comparação Normalizada (0=Pior, 1=Melhor)', fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(graficos_dir / '5_comparacao_geral.png', dpi=300, bbox_inches='tight')
    print("✅ Gráfico 5: Comparação Geral")
    plt.close()
    
    # ========== TABELA RESUMO (para slides) ==========
    print("\n" + "="*70)
    print("📋 TABELA RESUMO (copie para os slides)")
    print("="*70)
    
    resumo_final = df_llm.groupby('provider').agg({
        'tempo_total_ms': ['mean', 'std'],
        'num_citacoes': 'mean',
        'custo_estimado_usd': 'sum'
    }).round(2)
    
    resumo_final.columns = ['Tempo Médio (ms)', 'Desvio Padrão', 'Citações Médias', 'Custo Total (USD)']
    print(resumo_final.to_string())
    
    print("\n" + "="*70)
    print(f"✅ Gráficos salvos em: {graficos_dir}/")
    print("="*70)


if __name__ == "__main__":
    criar_graficos()
