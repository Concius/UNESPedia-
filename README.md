# 🔬 UNESPedia

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python" alt="Python Version" />
  <img src="https://img.shields.io/badge/Streamlit-Framework-red?logo=streamlit" alt="Framework" />
  <img src="https://img.shields.io/badge/Arquitetura-Modular-yellow" alt="Arquitetura Modular" />
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License" />
</div>

<div align="center">
  <h3>Converse com Seus Artigos de Forma Inteligente</h3>
</div>

## 📖 Sobre o Projeto

O **UNESPedia** é uma aplicação web desenvolvida como parte da disciplina de Aprendizado Profundo do PPGCC-Unesp. Ele utiliza a técnica de **Retrieval-Augmented Generation (RAG)** para permitir que você converse com os seus próprios documentos, transformando artigos densos em diálogos interativos.

Construído com uma arquitetura modular e flexível, o UNESPedia é uma ferramenta poderosa para pesquisadores, estudantes e qualquer pessoa que precise extrair informações e insights de uma base de documentos de forma rápida e intuitiva.


## 🏗️ Arquitetura do Sistema

### Stack Tecnológico

**Interface:**
- Streamlit - Framework web em Python para interfaces interativas

**Processamento de Documentos:**
- PyPDF - Extração de texto de PDFs
- Sentence-Transformers - Embeddings multilíngues (paraphrase-multilingual-mpnet-base-v2, 768 dimensões)

**Armazenamento Vetorial:**
- ChromaDB - Persistente em disco, ideal para produção
- FAISS - Em memória, otimizado para desenvolvimento

**Modelos LLM Suportados:**
- Google Gemini 2.5 Flash (1M tokens context window)
- Anthropic Claude Sonnet 4 (200K tokens context window)
- Deepseek Chat (64K tokens context window)
- OpenAI GPT (compatível via API)

**Gerenciamento:**
- Chaves API: `secrets.json` (local, não versionado)
- Configuração: `config.yaml` (centralizado)
- Histórico: JSON persistente por conversa

### Pipeline RAG

1. **Upload de PDF** - Usuário carrega documentos
2. **Extração de Texto** - PyPDF processa os PDFs
3. **Divisão em Chunks** - Texto dividido com overlap configurável
4. **Geração de Embeddings** - Modelo multilíngue cria vetores
5. **Armazenamento Vetorial** - ChromaDB ou FAISS indexa os chunks
6. **Query do Usuário** - Pergunta submetida
7. **Busca Semântica** - Top-k retrieval nos embeddings
8. **Geração com Contexto** - LLM recebe chunks relevantes
9. **Resposta com Citações** - Formato acadêmico (Fonte, p. X, sec. Y)

## ✨ Funcionalidades Principais


### 🤖 RAG com Citações Automáticas
- Sistema de busca semântica em múltiplos documentos
- Citações automáticas no formato acadêmico: (Fonte, p. X, sec. Y)
- Top-k retrieval configurável para melhor contexto

### 🔌 Arquitetura Multi-LLM
- Troca entre modelos em tempo real com um simples seletor
- Suporte para múltiplos provedores simultaneamente
- Configuração individual por provedor (temperatura, top-p, top-k)

### ✍️ System Prompt Editável
O aplicativo permite customização completa do comportamento do assistente através de um editor integrado.

**Prompt padrão:**
```
Você é um assistente de pesquisa acadêmica. 
Responda baseando-se APENAS no Contexto e Histórico fornecidos.

IMPORTANTE: sempre cite as fontes usando o formato:
(Fonte, p. {page}, sec. {section})

Se a informação de página ou seção não estiver disponível, omita esse campo.
```

**Recursos do editor:**
- Editor de texto completo na interface
- Preview com métricas (tokens, caracteres, linhas)
- Exportar/importar configurações
- Reset para padrão

### 🎭 Personas Customizáveis
**7 personas pré-definidas:**
1. Pesquisador Acadêmico
2. Professor Universitário
3. Analista Técnico
4. Fact-Checker Rigoroso
5. Revisor de Literatura
6. Consultor de Pesquisa
7. Especialista em Metodologia

**Recursos:**
- Criar personas customizadas
- Editor de prompts por persona
- Salvar e carregar configurações
- Gerenciar biblioteca de personas

### 👤 Perfil de Pesquisador
- Extração automática de metadados (autores, ano, título, DOI)
- Geração de perfil acadêmico via LLM
- Sistema de tags e categorização
- Biblioteca de perfis salvos com busca e filtros

### ⚙️ Presets de Configuração
Três presets pré-configurados para diferentes casos de uso:

**Preciso** (análises técnicas):
- Temperature: 0.2
- Top-p: 0.9
- Top-k: 20

**Equilibrado** (uso geral):
- Temperature: 0.7
- Top-p: 0.95
- Top-k: 40

**Criativo** (brainstorming):
- Temperature: 1.2
- Top-p: 0.98
- Top-k: 50

Todos os parâmetros são ajustáveis manualmente pela interface.

### 💬 Gestão Completa de Conversas
- **Salvamento Automático**: Cada conversa é salva automaticamente em JSON
- **Carregar e Continuar**: Carregue conversas anteriores e continue de onde parou
- **Renomear e Organizar**: Organize as suas sessões de chat diretamente pela interface
- **Apagar**: Remova conversas que não precisa mais

### 🔄 Histórico Interativo
- **Regenerar**: Não gostou da resposta? Gere uma nova com um clique
- **Editar**: Modifique qualquer mensagem (sua ou do assistente) para refinar o contexto
- **Apagar**: Remova mensagens individuais para limpar o histórico
- **Modo Debug**: Visualize os chunks recuperados e o processo de busca

## ⚙️ Hiperparâmetros


### Chunking
```
chunk_size: 512 tokens
chunk_overlap: 50 tokens
```

### Retrieval
```
n_results: 10 (top-k chunks recuperados)
```

### Embeddings
```
Modelo: paraphrase-multilingual-mpnet-base-v2
Dimensão: 768
Device: CPU/CUDA/MPS (detecção automática)
```

### Context Window por Modelo
```
Gemini 2.5 Flash: 1M tokens
Claude Sonnet 4: 200K tokens
Deepseek Chat: 64K tokens
```

## 🚀 Como Executar

### 1️⃣ Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes do Python)
- Git

### 2️⃣ Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/Concius/UNESPedia-.git

# 2. Acesse a pasta do projeto
cd UNESPedia-

# 3. Instale todas as dependências
pip install -r requirements.txt

# 4. Crie o diretório para salvar as conversas
mkdir chats
```

### 3️⃣ Configuração das Chaves de API

As chaves de API agora são geridas de forma persistente:

1. Execute a aplicação pela primeira vez: `streamlit run app.py`
2. Na barra lateral, selecione um provedor de LLM (ex: Gemini)
3. Cole a sua chave de API no campo correspondente
4. A chave será salva automaticamente no ficheiro `secrets.json`

> **⚠️ Importante**: O ficheiro `secrets.json` está incluído no `.gitignore` para garantir que as suas chaves nunca sejam enviadas para o repositório.

### 4️⃣ Executando a Aplicação

```bash
streamlit run app.py
```

A aplicação será aberta automaticamente no seu navegador. Agora, basta carregar os seus PDFs, processá-los e começar a sua pesquisa!

## 🛠️ Estrutura do Projeto


O código é organizado de forma modular para facilitar a manutenção e a adição de novas funcionalidades:

```
UNESPedia/
├── app.py                 # Ponto de entrada da aplicação (UI Streamlit)
├── config.yaml           # Configurações centrais (modelos, presets, etc.)
├── rag_processor.py      # Lógica de RAG (divisão de texto em chunks, embeddings)
├── llm_providers/        # Módulos para cada provedor de LLM
│   ├── gemini.py
│   ├── openai_provider.py
│   ├── claude.py
│   └── deepseek.py
├── vector_stores/        # Módulos para bases de dados vetoriais
│   ├── chroma_store.py
│   └── faiss_store.py
├── chat_manager.py       # Gestão de ficheiros de conversa
├── secrets_manager.py    # Gestão de chaves de API
├── prompt_manager.py     # Gestão de prompts e personas
├── requirements.txt      # Dependências do projeto
└── README.md
```

## 📊 Avaliação Experimental

O sistema foi avaliado comparando **3 LLMs** (Gemini 2.5 Flash, Claude Sonnet 4, Deepseek) e **2 vector stores** (ChromaDB, FAISS) utilizando um dataset de 3 PDFs sobre segurança e machine learning com 7 perguntas factuais.

### Métricas Avaliadas
- ⏱️ Tempo de resposta total
- 📝 Qualidade de citações
- 💰 Custo por consulta
- 🗄️ Tempo de indexação

### Configuração dos Testes
```
Temperature: 0.7
Top-p: 0.95
Top-k: 40
Max tokens: 2048
```

### Scripts Disponíveis
Os scripts de avaliação estão disponíveis em `/avaliacao/`:
- `avaliar_sistema.py` - Script principal de testes automatizados
- `visualizar_resultados.py` - Geração de gráficos e análises
- `README_AVALIACAO.md` - Documentação completa da metodologia

## 📜 Licença

**MIT License**

### Permissões
- ✅ Modificação
- ✅ Distribuição
- ✅ Uso privado

**Uso livre e irrestrito pela comunidade Unesp** (alunos, professores e funcionários).

## 💡 Sugestões & Contribuições

Este projeto está em constante evolução. Sinta-se à vontade para:

- 🐛 **Reportar bugs** abrindo uma issue
- 💡 **Sugerir melhorias** através de issues
- 🔧 **Contribuir com código** enviando pull requests

Toda colaboração é bem-vinda para tornar o UNESPedia ainda mais útil para a comunidade acadêmica!

---

<div align="center">
  <p><strong>Desenvolvido para a disciplina de Aprendizado Profundo - PPGCC Unesp</strong></p>
  <p>Feito com 💙</a></p>
</div>
