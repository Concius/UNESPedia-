# 🔬 UNESPedia

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python" alt="Python Version" />
  <img src="https://img.shields.io/badge/Streamlit-Framework-red?logo=streamlit" alt="Framework" />
  <img src="https://img.shields.io/badge/Arquitetura-Modular-yellow" alt="Arquitetura Modular" />
</div>

<div align="center">
  <h3>Converse com Seus Artigos de Forma Inteligente</h3>
</div>

---

## 📖 Sobre o Projeto

O **UNESPedia** é uma aplicação web desenvolvida como parte da disciplina de Aprendizado Profundo do PPGCC-Unesp. Ele utiliza a técnica de **Geração Aumentada por Recuperação (RAG)** para permitir que você converse com os seus próprios documentos, transformando artigos densos em diálogos interativos.

Construído com uma arquitetura modular e flexível, o UNESPedia é uma ferramenta poderosa para pesquisadores, estudantes e qualquer pessoa que precise extrair informações e insights de uma base de documentos de forma rápida e intuitiva.

## ✨ Funcionalidades Principais

O projeto evoluiu de um simples script para uma plataforma robusta com funcionalidades avançadas:

### 🔌 Arquitetura Multi-LLM
- Conecte-se a múltiplos provedores de LLM, como Gemini, OpenAI (GPT), Claude, Deepseek e Moonshot
- A troca entre modelos é feita com um simples seletor na interface

### 🗄️ Múltiplas Bases Vetoriais (Vector Stores)
- Suporte para ChromaDB (persistente em disco) e FAISS (rápido, em memória)
- A arquitetura permite adicionar novos vector stores facilmente

### 🔑 Gestão de Chaves API Persistente
- As suas chaves de API são salvas localmente no ficheiro `secrets.json`
- Não precisa inserir as chaves a cada sessão

### 💬 Gestão Completa de Conversas
- **Salvamento Automático**: Cada conversa é salva automaticamente após a resposta do assistente
- **Carregar e Continuar**: Carregue conversas anteriores e continue de onde parou
- **Renomear e Apagar**: Organize as suas sessões de chat diretamente pela interface

### ✍️ Histórico de Chat Interativo
- **Regenerar**: Não gostou da resposta? Peça ao assistente para gerar uma nova com um clique
- **Editar**: Modifique qualquer mensagem (sua ou do assistente) para refinar o contexto da conversa
- **Apagar**: Remova mensagens individuais para limpar o histórico

### 🧠 Configuração Avançada
- **Presets do LLM**: Alterne rapidamente entre configurações "Precisa", "Equilibrada" e "Criativa"
- **Ajuste Fino**: Controle manual de parâmetros como Temperature, Top-p e Top-k
- **Modo Depuração**: Ative para ver em detalhes o que acontece "por trás dos panos"

### 📄 Upload e Processamento de PDFs
- Carregue múltiplos artigos científicos para construir a sua base de conhecimento

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

## 🛠️ Estrutura do Projeto (Para Colaboradores)

O código é organizado de forma modular para facilitar a manutenção e a adição de novas funcionalidades:

```
UNESPedia/
├── app.py                 # Ponto de entrada da aplicação (UI Streamlit)
├── config.yaml           # Configurações centrais (modelos, presets, etc.)
├── rag_processor.py      # Lógica de RAG (divisão de texto em chunks)
├── llm_providers/        # Módulos para cada provedor de LLM
├── vector_stores/        # Módulos para bases de dados vetoriais
├── chat_manager.py       # Gestão de ficheiros de conversa
├── secrets_manager.py    # Gestão de chaves de API
└── requirements.txt      # Dependências do projeto
```

## 💡 Sugestões & Contribuições

Este projeto está em constante evolução. Sinta-se à vontade para:

- 🐛 **Reportar bugs** abrindo uma issue
- 💡 **Sugerir melhorias** através de issues
- 🔧 **Contribuir com código** enviando pull requests

Toda colaboração é bem-vinda para tornar o UNESPedia ainda mais útil para a comunidade acadêmica!

---

<div align="center">
  Feito com 💙 por <a href="https://github.com/Concius">Concius</a>
</div>
