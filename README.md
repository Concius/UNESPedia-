# UNESPedia-

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python" alt="Python Version" />
  <img src="https://img.shields.io/badge/Streamlit-Web%20App-red?logo=streamlit" alt="Streamlit" />
</div>

## 🔬 UNESPedia: Converse com Seus Artigos

Este projeto foi desenvolvido como parte da disciplina de **Aprendizado Profundo** do Programa de Pós-Graduação em Ciência da Computação (PPGCC) da Unesp, sob orientação do Prof. Dr. Denis Henrique de Oliveira.

---

## 📖 Sobre o Projeto

O **UNESPedia** é uma aplicação web que utiliza a técnica de **Geração Aumentada por Recuperação (RAG)** para permitir que você converse com seus próprios documentos. Basta fazer o upload de artigos científicos em PDF, e obtenha respostas inteligentes e contextualizadas.

> Uma ferramenta poderosa para pesquisadores, estudantes e qualquer pessoa que precise extrair informações e insights de uma base de documentos de forma rápida e intuitiva.

---

## ✨ Funcionalidades

- **Upload de Múltiplos PDFs**  
  Carregue um ou mais artigos científicos para análise.

- **Processamento Inteligente**  
  O texto é dividido em blocos (*chunks*) otimizados para análise pelo LLM.

- **Busca Semântica**  
  Encontre os trechos mais relevantes dos documentos para responder às suas perguntas.

- **Interface de Chat**  
  Converse de forma fluida com seus documentos, mantendo o contexto do histórico.

- **Modo Depuração (Debug)**  
  Veja em detalhes o que acontece "por trás dos panos", da divisão do texto ao prompt enviado ao modelo.

- **Configuração Avançada do LLM**  
  Ajuste os parâmetros do modelo (Temperature, Top-p, Top-k, Max Output Tokens) para controlar criatividade e estilo das respostas.

---

## 🚀 Como Executar

### 1️⃣ Pré-requisitos

- Python **3.8 ou superior**
- **pip** (gerenciador de pacotes do Python)

### 2️⃣ Instalação

```bash
# Clone o repositório
git clone https://github.com/Concius/UNESPedia-.git

# Acesse a pasta do projeto
cd UNESPedia-

# Instale as dependências
pip install -r requirements.txt
```

### 3️⃣ Configuração da API

Para usar o modelo Gemini, obtenha uma chave de API do [Google AI Studio](https://aistudio.google.com/):

1. Acesse o Google AI Studio e crie uma nova chave de API.
2. Copie a chave gerada.
3. Insira a chave diretamente na interface da aplicação ao iniciar.

### 4️⃣ Executando a Aplicação

```bash
streamlit run app.py
```

A aplicação será aberta automaticamente em seu navegador padrão.  
Agora, basta inserir sua chave de API, fazer upload dos PDFs e começar a conversar!

---

## 💡 Sugestões & Contribuições

Sinta-se à vontade para abrir issues e enviar pull requests!  
Toda colaboração é bem-vinda para tornar o UNESPedia ainda mais útil para a comunidade acadêmica.

---

<div align="center">
  <img src="https://img.shields.io/badge/Feito%20com%20💙%20por-Concius-blue" />
</div>
