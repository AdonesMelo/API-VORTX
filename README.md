# 🚀 API-VORTX

Uma API desenvolvida em Python com o objetivo de facilitar integrações e automatizações utilizando a plataforma VORTX.

## 📌 Funcionalidades

- Autenticação com a API da VORTX
- Consulta de dados financeiros
- Integração com sistemas externos
- Utilitários para manipulação de dados

## 🛠 Tecnologias Utilizadas

- Python 3.x
- Requests
- python-dotenv
- SQL Server
- Outras dependências listadas em `requirements.txt`

## ⚙️ Configuração do Ambiente

Antes de executar a aplicação, **crie um arquivo `.env`** na raiz do projeto com as credenciais necessárias para autenticação da API e conexão com o banco de dados.

### Exemplo de `.env`:

```env
# Credenciais da API VORTX
VORTX_TOKEN=seu_token_aqui
VORTX_LOGIN=sua_senha_secreta

# Configuração do SQL Server
DB_SERVER=localhost
DB_NAME=nome_do_banco
DB_USER=usuario
DB_PASS=senha

🔒 Importante: Certifique-se de que o arquivo .env esteja listado no .gitignore para evitar o versionamento de informações sensíveis.


## 📦 Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/AdonesMelo/API-VORTX.git

2. Instale as dependências:
   ```bash
    pip install -r requirements.txt

3. Execute a aplicação:
   ```bash
    python app.py

4. 📁 Estrutura do Projeto
   ```Código
    API-VORTX/
    ├── app.py
    ├── requirements.txt
    ├── Util/
    │   └── funcoes_utilitarias.py
    └── .gitignore





