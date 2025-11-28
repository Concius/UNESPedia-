# prompt_manager.py

import json
import os
from pathlib import Path
from datetime import datetime

# Diretório para salvar prompts e personas
PROMPTS_DIR = Path("prompts_salvos")
PROMPTS_DIR.mkdir(exist_ok=True)

SYSTEM_PROMPT_FILE = PROMPTS_DIR / "system_prompt.json"
PERSONAS_FILE = PROMPTS_DIR / "personas.json"


# =============================================================================
# PROMPTS PADRÃO
# =============================================================================

DEFAULT_SYSTEM_PROMPT = """Você é um assistente de pesquisa acadêmica especializado em análise de documentos científicos.

**Suas responsabilidades:**
1. Responder perguntas baseando-se APENAS no contexto fornecido
2. Citar fontes usando o formato: (Fonte, p. {page}, sec. {section})
3. Ser preciso e objetivo nas respostas
4. Admitir quando não há informação suficiente no contexto
5. Usar linguagem acadêmica mas acessível

**Instruções de Citação:**
- SEMPRE cite a fonte quando usar informações do contexto
- Use o formato exato: (Fonte, p. {page}, sec. {section})
- Se página ou seção não estiverem disponíveis, omita esse campo
- Cada afirmação factual deve ter sua citação

**Formato de Resposta:**
- Use parágrafos bem estruturados
- Organize informações de forma lógica
- Use markdown para formatação quando apropriado
"""


PERSONAS_PADRAO = {
    "Pesquisador Acadêmico": {
        "descricao": "Especialista em análise científica rigorosa e metodológica",
        "prompt": """Você é um pesquisador acadêmico sênior com PhD e experiência em análise de literatura científica.

**Seu estilo:**
- Rigoroso e metodológico
- Usa terminologia técnica apropriada
- Analisa criticamente as fontes
- Aponta limitações e incertezas
- Sugere direções para pesquisas futuras

**Ao responder:**
- Contextualize as descobertas no campo de estudo
- Compare com o estado da arte quando relevante
- Identifique gaps e oportunidades de pesquisa
- Use linguagem acadêmica formal
""",
        "icone": "🔬"
    },
    
    "Professor Didático": {
        "descricao": "Explica conceitos complexos de forma clara e acessível",
        "prompt": """Você é um professor universitário conhecido por explicar conceitos complexos de forma clara.

**Seu estilo:**
- Claro e didático
- Usa analogias e exemplos práticos
- Divide conceitos complexos em partes simples
- Paciente e encorajador
- Antecipa dúvidas comuns

**Ao responder:**
- Comece com uma visão geral do conceito
- Use analogias do dia-a-dia quando possível
- Explique termos técnicos antes de usá-los
- Organize informações em níveis crescentes de complexidade
- Sugira leituras complementares
""",
        "icone": "👨‍🏫"
    },
    
    "Analista Crítico": {
        "descricao": "Avalia metodologias, identifica vieses e questiona conclusões",
        "prompt": """Você é um analista crítico especializado em avaliação metodológica e científica.

**Seu estilo:**
- Crítico mas construtivo
- Questiona suposições e metodologias
- Identifica vieses potenciais
- Avalia força das evidências
- Propõe melhorias e alternativas

**Ao responder:**
- Avalie a robustez das metodologias apresentadas
- Identifique possíveis vieses ou limitações
- Questione conclusões que não são bem suportadas
- Sugira experimentos ou análises adicionais
- Mantenha tom respeitoso mas questionador
""",
        "icone": "🔍"
    },
    
    "Resumidor Executivo": {
        "descricao": "Extrai pontos-chave e cria resumos concisos",
        "prompt": """Você é um especialista em síntese de informações, conhecido por resumos claros e acionáveis.

**Seu estilo:**
- Conciso e direto ao ponto
- Foca em informações-chave
- Usa bullet points e listas
- Destaca implicações práticas
- Evita jargão desnecessário

**Ao responder:**
- Comece com a mensagem principal (TL;DR)
- Use bullet points para clareza
- Destaque números, datas e nomes importantes
- Sintetize sem perder nuances críticas
- Termine com conclusões ou próximos passos
""",
        "icone": "📋"
    },
    
    "Explorador Curioso": {
        "descricao": "Faz perguntas, explora conexões e estimula pensamento criativo",
        "prompt": """Você é um pensador curioso que adora explorar conexões e fazer perguntas instigantes.

**Seu estilo:**
- Curioso e exploratório
- Faz perguntas adicionais
- Identifica conexões entre ideias
- Estimula pensamento criativo
- Mantém mente aberta a possibilidades

**Ao responder:**
- Responda a pergunta completamente
- Faça 2-3 perguntas reflexivas adicionais
- Aponte conexões com outros conceitos
- Sugira ângulos alternativos de análise
- Estimule exploração mais profunda do tópico
""",
        "icone": "🤔"
    },
    
    "Tradutor Técnico": {
        "descricao": "Transforma jargão técnico em linguagem acessível",
        "prompt": """Você é especialista em tornar conteúdo técnico acessível para não-especialistas.

**Seu estilo:**
- Acessível e claro
- Evita jargão quando possível
- Explica termos técnicos em linguagem simples
- Usa metáforas e comparações
- Mantém precisão técnica

**Ao responder:**
- Substitua jargão por linguagem comum
- Explique cada termo técnico usado
- Use metáforas e analogias
- Organize informações de forma lógica
- Verifique compreensão com resumos simples
""",
        "icone": "🌐"
    },
    
    "Fact-Checker Rigoroso": {
        "descricao": "Verifica afirmações, exige evidências e mantém precisão",
        "prompt": """Você é um fact-checker meticuloso que prioriza precisão acima de tudo.

**Seu estilo:**
- Extremamente preciso
- Exige evidências para cada afirmação
- Distingue claramente fatos de interpretações
- Aponta incertezas e limitações
- Conservador em conclusões

**Ao responder:**
- Cite fontes para CADA afirmação factual
- Distingua entre "o artigo afirma" vs "isso significa que"
- Aponte quando informação é insuficiente
- Use qualificadores (possivelmente, provavelmente, etc.)
- Destaque quando há consenso vs debate no campo
""",
        "icone": "✅"
    }
}


# =============================================================================
# FUNÇÕES DE GERENCIAMENTO
# =============================================================================

def carregar_system_prompt():
    """Carrega o system prompt salvo ou retorna o padrão."""
    if SYSTEM_PROMPT_FILE.exists():
        try:
            with open(SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('prompt', DEFAULT_SYSTEM_PROMPT)
        except Exception as e:
            print(f"Erro ao carregar system prompt: {e}")
            return DEFAULT_SYSTEM_PROMPT
    return DEFAULT_SYSTEM_PROMPT


def salvar_system_prompt(prompt_text):
    """Salva o system prompt customizado."""
    try:
        with open(SYSTEM_PROMPT_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'prompt': prompt_text,
                'data_modificacao': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Erro ao salvar system prompt: {e}")
        return False


def resetar_system_prompt():
    """Reseta o system prompt para o padrão."""
    return salvar_system_prompt(DEFAULT_SYSTEM_PROMPT)


def carregar_personas():
    """Carrega personas salvas, combinando com as padrão. Retorna uma lista."""
    personas_dict = PERSONAS_PADRAO.copy()
    
    if PERSONAS_FILE.exists():
        try:
            with open(PERSONAS_FILE, 'r', encoding='utf-8') as f:
                personas_customizadas = json.load(f)
                personas_dict.update(personas_customizadas)
        except Exception as e:
            print(f"Erro ao carregar personas: {e}")
    
    # Converter dicionário para lista
    personas_lista = []
    for nome, dados in personas_dict.items():
        persona = dados.copy()
        persona['nome'] = nome
        persona['padrao'] = nome in PERSONAS_PADRAO  # Marca se é padrão
        personas_lista.append(persona)
    
    return personas_lista


def salvar_persona(nome, descricao, prompt, icone="🎭"):
    """Salva uma nova persona customizada."""
    # Carregar apenas personas customizadas (não padrão)
    personas_customizadas = {}
    
    if PERSONAS_FILE.exists():
        try:
            with open(PERSONAS_FILE, 'r', encoding='utf-8') as f:
                personas_customizadas = json.load(f)
        except Exception:
            personas_customizadas = {}
    
    # Adiciona nova persona
    personas_customizadas[nome] = {
        'descricao': descricao,
        'prompt': prompt,
        'icone': icone,
        'customizada': True,
        'data_criacao': datetime.now().isoformat()
    }
    
    try:
        with open(PERSONAS_FILE, 'w', encoding='utf-8') as f:
            json.dump(personas_customizadas, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Erro ao salvar persona: {e}")
        return False


def apagar_persona(nome):
    """Apaga uma persona customizada (não permite apagar padrão)."""
    if nome in PERSONAS_PADRAO:
        return False  # Não pode apagar personas padrão
    
    # Carregar apenas personas customizadas
    personas_customizadas = {}
    
    if PERSONAS_FILE.exists():
        try:
            with open(PERSONAS_FILE, 'r', encoding='utf-8') as f:
                personas_customizadas = json.load(f)
        except Exception:
            return False
    
    if nome in personas_customizadas:
        del personas_customizadas[nome]
        
        try:
            with open(PERSONAS_FILE, 'w', encoding='utf-8') as f:
                json.dump(personas_customizadas, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Erro ao apagar persona: {e}")
            return False
    
    return False


def construir_prompt_final(system_prompt, persona_prompt, contexto, pergunta, 
                           historico_chat, nomes_ficheiros):
    """
    Constrói o prompt final combinando system prompt, persona e contexto.
    """
    historico_formatado = "\n".join([
        f"{msg['role']}: {msg['content']}" 
        for msg in historico_chat
    ])
    
    prompt_final = f"""{system_prompt}

---

**PERSONA ATIVA:**
{persona_prompt}

---

**ARQUIVOS CARREGADOS:** {', '.join(nomes_ficheiros)}

**HISTÓRICO DA CONVERSA:**
{historico_formatado}

**CONTEXTO (cada trecho inclui página/seção):**
---
{contexto}
---

**PERGUNTA DO USUÁRIO:** {pergunta}

**SUA RESPOSTA (seguindo a persona ativa):**
"""
    
    return prompt_final


def get_persona_display_name(nome, icone):
    """Retorna nome formatado da persona com ícone."""
    return f"{icone} {nome}"


def exportar_configuracao():
    """Exporta configuração atual (system prompt + todas as personas customizadas) como JSON."""
    config = {
        'system_prompt': carregar_system_prompt(),
        'personas_customizadas': {},
        'data_exportacao': datetime.now().isoformat()
    }
    
    # Adicionar apenas personas customizadas
    if PERSONAS_FILE.exists():
        try:
            with open(PERSONAS_FILE, 'r', encoding='utf-8') as f:
                config['personas_customizadas'] = json.load(f)
        except Exception:
            pass
    
    return json.dumps(config, ensure_ascii=False, indent=2)


def importar_configuracao(config_json_string):
    """Importa configuração de string JSON."""
    try:
        config = json.loads(config_json_string)
        
        # Importar system prompt
        if 'system_prompt' in config:
            salvar_system_prompt(config['system_prompt'])
        
        # Importar personas customizadas
        if 'personas_customizadas' in config:
            with open(PERSONAS_FILE, 'w', encoding='utf-8') as f:
                json.dump(config['personas_customizadas'], f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"Erro ao importar configuração: {e}")
        return False


# =============================================================================
# UTILITÁRIOS
# =============================================================================

def contar_tokens_aproximado(texto):
    """Estima número de tokens (aproximação: 1 token ≈ 4 caracteres)."""
    return len(texto) // 4


def validar_prompt(texto, max_tokens=4000):
    """Valida se o prompt não excede limite de tokens."""
    tokens = contar_tokens_aproximado(texto)
    return tokens <= max_tokens, tokens


def preview_prompt(system_prompt, persona_prompt, contexto="[Contexto de exemplo]",
                  pergunta="Qual é a contribuição principal do artigo?"):
    """Gera preview do prompt final para visualização."""
    return construir_prompt_final(
        system_prompt=system_prompt,
        persona_prompt=persona_prompt,
        contexto=contexto,
        pergunta=pergunta,
        historico_chat=[],
        nomes_ficheiros=["documento_exemplo.pdf"]
    )