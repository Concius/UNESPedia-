# UNESPedia-

🔬 UNESPedia: Converse com Seus Artigos
Este projeto foi desenvolvido como parte da disciplina de "Aprendizado Profundo" do Programa de Pós-Graduação em Ciência da Computação (PPGCC) da Unesp, sob a orientação do Prof. Dr. Denis Henrique Pinheiro Salvadeo.

📖 Sobre o Projeto
O UNESPedia é uma aplicação web que utiliza a técnica de Geração Aumentada por Recuperação (RAG) para permitir que você converse com seus próprios documentos. Basta fazer o upload de artigos em formato PDF, e a aplicação irá processá-los e utilizar um Grande Modelo de Linguagem (LLM), como o Gemini, para responder perguntas com base no conteúdo dos textos.

É uma ferramenta poderosa para pesquisadores, estudantes e qualquer pessoa que precise extrair informações e insights de uma base de documentos de forma rápida e intuitiva.

✨ Funcionalidades
Upload de Múltiplos PDFs: Carregue um ou mais artigos científicos para análise.

Processamento Inteligente: O texto é dividido em blocos (chunks) otimizados para a análise do LLM.

Busca Semântica: Encontre os trechos mais relevantes nos documentos para responder às suas perguntas.

Interface de Chat: Converse de forma fluida com seus documentos, com o histórico da conversa sendo utilizado para manter o contexto.

Modo Depuração (Debug): Visualize em detalhes o que está acontecendo por trás dos panos, desde a divisão do texto até o prompt enviado ao modelo.

Configuração Avançada do LLM: Ajuste fino dos parâmetros do modelo (Temperature, Top-p, Top-k, Max Output Tokens) diretamente na interface para controlar a criatividade e o estilo das respostas.

🚀 Como Executar
Para colocar a aplicação em funcionamento, siga os passos abaixo.

#1. Pré-requisitos
Python 3.8 ou superior

pip (gerenciador de pacotes do Python)

#2. Instalação
Primeiro, clone este repositório e instale as dependências necessárias:

Bash

Clone o repositório
git clone https://https://github.com/Concius/UNESPedia-.git

cd UNESPedia

Instale as dependências a partir do arquivo requirements.txt
pip install -r requirements.txt
3. Configuração da API
Para que a aplicação se comunique com o modelo Gemini, você precisa de uma chave de API do Google AI Studio.

Acesse o Google AI Studio.

Crie uma nova chave de API ("Create API key").

Copie a chave gerada.

Você irá inserir essa chave diretamente na interface da aplicação ao iniciá-la.

#4. Executando a Aplicação
Com as dependências instaladas, inicie o servidor do Streamlit com o seguinte comando:

Bash

streamlit run app.py
A aplicação será aberta automaticamente no seu navegador padrão. Agora, basta inserir sua chave de API, fazer o upload dos seus PDFs e começar a conversar!

