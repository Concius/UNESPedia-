# profile_manager.py
"""
Sistema de gerenciamento de perfis de pesquisadores.
Permite salvar, carregar, buscar e organizar perfis com tags.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
import re

# Diretório para salvar perfis
PERFIS_DIR = "perfis_salvos"

def inicializar_diretorio_perfis():
    """Garante que o diretório de perfis existe."""
    if not os.path.exists(PERFIS_DIR):
        os.makedirs(PERFIS_DIR)

def extrair_keywords_do_perfil(texto_perfil: str) -> List[str]:
    """
    Extrai keywords da seção 3 do perfil gerado.
    Procura por listas de palavras-chave no formato:
    "palavra1, palavra2, palavra3"
    """
    keywords = []
    
    # Padrão 1: Seção "Palavras-chave" com lista separada por vírgulas
    padrao1 = r'(?:##\s*3\.?\s*Palavras-chave.*?)\n(.*?)(?=\n##|\Z)'
    match = re.search(padrao1, texto_perfil, re.DOTALL | re.IGNORECASE)
    
    if match:
        texto_keywords = match.group(1)
        # Remove markdown e quebras de linha
        texto_limpo = re.sub(r'[*_`#-]', '', texto_keywords)
        texto_limpo = texto_limpo.replace('\n', ' ')
        
        # Split por vírgula
        palavras = [k.strip() for k in texto_limpo.split(',')]
        keywords.extend([k for k in palavras if k and len(k) > 2])
    
    # Padrão 2: Busca por listas com bullets
    padrao2 = r'[-•]\s*([a-zA-Z\s]+(?:\s+[a-zA-Z]+)*)'
    matches = re.finditer(padrao2, texto_perfil)
    for match in matches:
        keyword = match.group(1).strip()
        if 3 < len(keyword) < 50 and keyword not in keywords:
            keywords.append(keyword)
    
    # Limita a 20 keywords mais relevantes
    return keywords[:20]

def salvar_perfil(nome_pesquisador: str, 
                  perfil_texto: str, 
                  artigos: List[Dict],
                  keywords_artigos: List[str] = None) -> str:
    """
    Salva um perfil de pesquisador com metadados.
    
    Args:
        nome_pesquisador: Nome do pesquisador
        perfil_texto: Texto do perfil em Markdown
        artigos: Lista de dicionários com metadados dos artigos
        keywords_artigos: Keywords extraídas dos artigos
    
    Returns:
        str: Caminho do arquivo salvo
    """
    inicializar_diretorio_perfis()
    
    # Extrai keywords do perfil
    keywords_perfil = extrair_keywords_do_perfil(perfil_texto)
    
    # Combina keywords dos artigos e do perfil (sem duplicatas)
    if keywords_artigos:
        todas_keywords = list(set(keywords_artigos + keywords_perfil))
    else:
        todas_keywords = keywords_perfil
    
    # Cria estrutura do perfil
    perfil_completo = {
        'nome_pesquisador': nome_pesquisador,
        'data_criacao': datetime.now().isoformat(),
        'perfil_markdown': perfil_texto,
        'tags': todas_keywords,
        'artigos': [
            {
                'titulo': a.get('titulo', ''),
                'ano': a.get('ano'),
                'autores': a.get('autores', []),
                'fonte': a.get('fonte', ''),
                'abstract': a.get('abstract', '')[:500]  # Limita abstract
            }
            for a in artigos
        ],
        'estatisticas': {
            'num_artigos': len(artigos),
            'anos': [a.get('ano') for a in artigos if a.get('ano')],
            'num_coautores': len(set(
                autor 
                for a in artigos 
                for autor in a.get('autores', [])
            )) - 1  # Exclui o próprio pesquisador
        }
    }
    
    # Nome do arquivo (sanitizado)
    nome_arquivo = nome_pesquisador.replace(' ', '_').replace('.', '')
    nome_arquivo = re.sub(r'[^\w\-]', '', nome_arquivo)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = os.path.join(PERFIS_DIR, f"{nome_arquivo}_{timestamp}.json")
    
    # Salva
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(perfil_completo, f, ensure_ascii=False, indent=2)
    
    return filepath

def listar_perfis_salvos() -> List[Dict]:
    """
    Lista todos os perfis salvos com seus metadados.
    
    Returns:
        Lista de dicionários com: nome, data, tags, num_artigos, filepath
    """
    inicializar_diretorio_perfis()
    
    perfis = []
    
    for filename in os.listdir(PERFIS_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(PERFIS_DIR, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    perfil_data = json.load(f)
                
                perfis.append({
                    'nome': perfil_data.get('nome_pesquisador', 'Desconhecido'),
                    'data': perfil_data.get('data_criacao', ''),
                    'tags': perfil_data.get('tags', []),
                    'num_artigos': perfil_data.get('estatisticas', {}).get('num_artigos', 0),
                    'filepath': filepath,
                    'anos': perfil_data.get('estatisticas', {}).get('anos', [])
                })
            except Exception as e:
                # Se houver erro ao ler, pula o arquivo
                continue
    
    # Ordena por data (mais recente primeiro)
    perfis.sort(key=lambda x: x['data'], reverse=True)
    
    return perfis

def carregar_perfil(filepath: str) -> Optional[Dict]:
    """
    Carrega um perfil completo de um arquivo.
    
    Args:
        filepath: Caminho do arquivo JSON
    
    Returns:
        Dicionário com todos os dados do perfil ou None se erro
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None

def apagar_perfil(filepath: str) -> bool:
    """
    Apaga um perfil salvo.
    
    Args:
        filepath: Caminho do arquivo JSON
    
    Returns:
        True se sucesso, False caso contrário
    """
    try:
        os.remove(filepath)
        return True
    except Exception:
        return False

def buscar_perfis(query: str, perfis: List[Dict]) -> List[Dict]:
    """
    Busca perfis por nome ou tags.
    
    Args:
        query: Texto de busca
        perfis: Lista de perfis (retorno de listar_perfis_salvos)
    
    Returns:
        Lista filtrada de perfis
    """
    if not query or not query.strip():
        return perfis
    
    query_lower = query.lower().strip()
    resultados = []
    
    for perfil in perfis:
        # Busca no nome
        if query_lower in perfil['nome'].lower():
            resultados.append(perfil)
            continue
        
        # Busca nas tags
        tags_str = ' '.join(perfil.get('tags', [])).lower()
        if query_lower in tags_str:
            resultados.append(perfil)
            continue
    
    return resultados

def exportar_perfil_markdown(perfil_data: Dict) -> str:
    """
    Gera arquivo Markdown completo do perfil para download.
    
    Args:
        perfil_data: Dicionário com dados do perfil
    
    Returns:
        String com conteúdo Markdown
    """
    md = f"""# Perfil Científico: {perfil_data['nome_pesquisador']}

**Data de geração:** {perfil_data['data_criacao'][:10]}

---

{perfil_data['perfil_markdown']}

---

## 📊 Estatísticas

- **Total de artigos analisados:** {perfil_data['estatisticas']['num_artigos']}"""
    
    # Adiciona período apenas se houver anos
    anos = perfil_data['estatisticas']['anos']
    if anos:
        md += f"\n- **Período de publicação:** {min(anos)} - {max(anos)}"
    else:
        md += f"\n- **Período de publicação:** Não disponível"
    
    md += f"""
- **Número de colaboradores únicos:** {perfil_data['estatisticas']['num_coautores']}

## 🏷️ Tags

{', '.join(perfil_data['tags'])}

## 📚 Artigos Analisados

"""
    
    for i, artigo in enumerate(perfil_data['artigos'], 1):
        md += f"\n### {i}. {artigo['titulo']}\n"
        md += f"- **Ano:** {artigo['ano'] if artigo['ano'] else 'N/A'}\n"
        md += f"- **Autores:** {', '.join(artigo['autores'][:3])}"
        if len(artigo['autores']) > 3:
            md += f" (e mais {len(artigo['autores']) - 3})"
        md += "\n\n"
    
    return md