# metadata_extractor_v2.py
"""
Módulo para extrair metadados de PDFs científicos.
Versão 2: Correções na detecção de autores.
"""

import re
from pypdf import PdfReader
import io

# ===== LISTA DE STOPWORDS PARA FILTRAR =====
LOCATION_KEYWORDS = [
    # Países
    'USA', 'UK', 'China', 'Japan', 'Germany', 'France', 'India', 'Brazil',
    # Estados dos EUA
    'California', 'New York', 'Texas', 'Florida', 'Illinois', 'Pennsylvania',
    'Ohio', 'Georgia', 'North Carolina', 'Michigan', 'New Jersey', 'Virginia',
    'Washington', 'Massachusetts', 'Tennessee', 'Indiana', 'Missouri', 'Maryland',
    'Wisconsin', 'Minnesota', 'Colorado', 'Alabama', 'South Carolina', 'Louisiana',
    'Kentucky', 'Oregon', 'Oklahoma', 'Connecticut', 'Iowa', 'Utah', 'Nevada',
    'Arkansas', 'Mississippi', 'Kansas', 'New Mexico', 'Nebraska', 'West Virginia',
    'Idaho', 'Hawaii', 'New Hampshire', 'Maine', 'Rhode Island', 'Montana',
    'Delaware', 'South Dakota', 'North Dakota', 'Alaska', 'Vermont', 'Wyoming',
    # Cidades comuns
    'York', 'London', 'Paris', 'Tokyo', 'Beijing', 'Berlin', 'Toronto',
    'Sydney', 'Melbourne', 'Madrid', 'Rome', 'Amsterdam', 'Cambridge',
    'Oxford', 'Stanford', 'Berkeley', 'Princeton', 'Hanover',
    # Palavras institucionais
    'University', 'College', 'Institute', 'Department', 'Laboratory', 'Center',
    'School', 'Faculty', 'Academy', 'Research', 'Lab', 'Inc', 'Corporation',
    'Company', 'Ltd', 'LLC', 'Group', 'Division', 'Office'
]

# ===== FUNÇÃO AUXILIAR: VERIFICAR SE É LOCALIZAÇÃO =====
def eh_localizacao(texto):
    """Verifica se o texto parece ser uma localização/afiliação ao invés de um nome."""
    texto_upper = texto.upper()
    
    # Verifica se contém palavras-chave de localização
    for keyword in LOCATION_KEYWORDS:
        if keyword.upper() in texto_upper:
            return True
    
    # Verifica se tem muitas palavras maiúsculas seguidas (típico de afiliações)
    palavras = texto.split()
    if len(palavras) > 1:
        maiusculas_count = sum(1 for p in palavras if p[0].isupper() if p)
        if maiusculas_count == len(palavras) and len(palavras) > 2:
            return True
    
    return False

# ===== EXTRAIR AUTORES (VERSÃO MELHORADA) =====
def extrair_autores_primeira_pagina(texto_primeira_pagina):
    """
    Extrai autores da primeira página com múltiplas estratégias e filtros.
    Retorna (lista_autores, primeiro_autor).
    """
    linhas = texto_primeira_pagina.split('\n')
    autores = []
    
    # --- ESTRATÉGIA 1: Procurar por padrões de autores com afiliações ---
    # Padrão: Nome Sobrenome seguido de número sobrescrito
    padrao_autor_com_afiliacao = r'^([A-Z][a-zà-ÿ]+\s+[A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)?)[*†‡§¶∗⁰¹²³⁴⁵⁶⁷⁸⁹]'
    
    for i, linha in enumerate(linhas[:30]):  # Busca nas primeiras 30 linhas
        linha = linha.strip()
        match = re.search(padrao_autor_com_afiliacao, linha)
        if match:
            nome_completo = match.group(1).strip()
            if not eh_localizacao(nome_completo):
                autores.append(nome_completo)
    
    # --- ESTRATÉGIA 2: Procurar por listas com vírgulas ---
    # Padrão: Nome Sobrenome, Nome2 Sobrenome2, Nome3 Sobrenome3
    if not autores:
        for i, linha in enumerate(linhas[:20]):
            # Pula linhas que parecem título (geralmente maiúsculas ou muito longas)
            if len(linha) > 80 or linha.isupper():
                continue
            
            # Procura padrão de lista de autores
            if ',' in linha and not any(x in linha.lower() for x in ['university', 'department', 'email', '@']):
                potenciais = re.findall(r'\b([A-Z][a-zà-ÿ]+\s+[A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)?)\b', linha)
                
                # Filtra localizações
                potenciais_filtrados = [nome for nome in potenciais if not eh_localizacao(nome)]
                
                if len(potenciais_filtrados) >= 2:  # Pelo menos 2 autores
                    autores.extend(potenciais_filtrados)
                    break
    
    # --- ESTRATÉGIA 3: Procurar nomes após o título ---
    if not autores:
        titulo_encontrado = False
        for i, linha in enumerate(linhas[:25]):
            linha = linha.strip()
            
            # Detecta fim do título (linha em branco ou linha curta)
            if titulo_encontrado and (len(linha) < 10 or linha == ''):
                continue
            
            if len(linha) > 40:  # Provavelmente parte do título
                titulo_encontrado = True
                continue
            
            # Após o título, procura nomes
            if titulo_encontrado and len(linha) > 5:
                potenciais = re.findall(r'\b([A-Z][a-zà-ÿ]+\s+[A-Z][a-zà-ÿ]+)\b', linha)
                
                for nome in potenciais:
                    if not eh_localizacao(nome) and nome not in autores:
                        autores.append(nome)
                
                # Se encontrou autores, para de buscar após mais 3 linhas
                if autores and i > 10:
                    break
    
    # --- LIMPEZA FINAL ---
    # Remove duplicados mantendo ordem
    autores = list(dict.fromkeys(autores))
    
    # Se não encontrou nenhum autor, retorna lista vazia
    if not autores:
        return [], "Autor Desconhecido"
    
    primeiro_autor = autores[0] if autores else "Autor Desconhecido"
    
    return autores, primeiro_autor

# ===== EXTRAIR TÍTULO =====
def extrair_titulo_primeira_pagina(texto_primeira_pagina):
    """Extrai título da primeira página (primeira linha não-vazia mais longa)."""
    linhas = texto_primeira_pagina.split('\n')
    titulo_candidato = ""
    
    for linha in linhas[:15]:  # Busca nas primeiras 15 linhas
        linha = linha.strip()
        if len(linha) > len(titulo_candidato) and len(linha) > 20:
            # Ignora linhas que parecem afiliação ou metadados
            if not any(x in linha.lower() for x in ['university', 'email', '@', 'abstract', 'keywords']):
                titulo_candidato = linha
    
    return titulo_candidato if titulo_candidato else "Título Desconhecido"

# ===== EXTRAIR ANO =====
def extrair_ano(texto):
    """Extrai o ano de publicação (busca anos entre 1900-2030)."""
    anos = re.findall(r'\b(19\d{2}|20[0-3]\d)\b', texto[:500])
    if anos:
        return int(anos[0])  # Retorna o primeiro ano encontrado
    return None

# ===== EXTRAIR ABSTRACT =====
def extrair_abstract(texto):
    """Extrai o abstract/resumo do artigo."""
    # Padrões comuns de início de abstract
    padroes_inicio = [
        r'(?i)abstract[:\s]*\n(.*?)(?=\n\n|\nkeywords|\nintroduction|\n1\s)',
        r'(?i)summary[:\s]*\n(.*?)(?=\n\n|\nkeywords|\nintroduction)',
        r'(?i)resumo[:\s]*\n(.*?)(?=\n\n|\npalavras-chave)'
    ]
    
    for padrao in padroes_inicio:
        match = re.search(padrao, texto[:3000], re.DOTALL)
        if match:
            abstract = match.group(1).strip()
            # Limita a 500 palavras
            palavras = abstract.split()[:500]
            return ' '.join(palavras)
    
    return "Abstract não encontrado"

# ===== FUNÇÃO PRINCIPAL: EXTRAIR METADADOS =====
def extrair_metadados_pdf(pdf_file_bytes, nome_arquivo):
    """
    Extrai metadados completos de um PDF científico.
    
    Args:
        pdf_file_bytes: Bytes do arquivo PDF
        nome_arquivo: Nome do arquivo (usado como fallback)
    
    Returns:
        dict com: fonte, titulo, autores, primeiro_autor, ano, abstract
    """
    try:
        # Lê o PDF
        pdf_reader = PdfReader(io.BytesIO(pdf_file_bytes))
        
        # Extrai texto da primeira página
        primeira_pagina = pdf_reader.pages[0]
        texto_primeira_pagina = primeira_pagina.extract_text()
        
        # Extrai texto completo (primeiras 3 páginas para abstract)
        texto_completo = ""
        for i in range(min(3, len(pdf_reader.pages))):
            texto_completo += pdf_reader.pages[i].extract_text()
        
        # Extrai cada metadado
        titulo = extrair_titulo_primeira_pagina(texto_primeira_pagina)
        autores, primeiro_autor = extrair_autores_primeira_pagina(texto_primeira_pagina)
        ano = extrair_ano(texto_completo)
        abstract = extrair_abstract(texto_completo)
        
        return {
            'fonte': nome_arquivo,
            'titulo': titulo,
            'autores': autores,
            'primeiro_autor': primeiro_autor,
            'ano': ano,
            'abstract': abstract
        }
    
    except Exception as e:
        # Em caso de erro, retorna metadados vazios
        return {
            'fonte': nome_arquivo,
            'titulo': "Erro na extração",
            'autores': [],
            'primeiro_autor': "Autor Desconhecido",
            'ano': None,
            'abstract': f"Erro ao extrair: {e}"
        }

# ===== FILTRAR ARTIGOS POR AUTOR =====
def filtrar_artigos_por_autor(lista_metadados, nome_pesquisador, threshold=0.7):
    """
    Filtra artigos onde o pesquisador é autor usando fuzzy matching.
    
    Args:
        lista_metadados: Lista de dicionários de metadados
        nome_pesquisador: Nome do pesquisador a buscar
        threshold: Limite de similaridade (0.0 a 1.0)
    
    Returns:
        Lista de metadados filtrados
    """
    from difflib import SequenceMatcher
    
    def similaridade(a, b):
        """Calcula similaridade entre duas strings."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    artigos_filtrados = []
    nome_pesquisador_lower = nome_pesquisador.lower()
    
    for meta in lista_metadados:
        for autor in meta['autores']:
            # Verifica similaridade
            sim = similaridade(nome_pesquisador_lower, autor.lower())
            
            # Ou verifica se o nome do pesquisador está contido no nome do autor
            if sim >= threshold or nome_pesquisador_lower in autor.lower():
                artigos_filtrados.append(meta)
                break  # Não precisa checar outros autores deste artigo
    
    return artigos_filtrados