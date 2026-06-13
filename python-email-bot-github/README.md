# Python Email Bot

Sistema desktop em Python para envio de e-mails em massa com interface gráfica, grupos de contatos, templates, anexos, imagens inline, agendamento e histórico.

## Funcionalidades

- Login com Gmail
- Criptografia local das credenciais
- Criação e remoção de grupos de contatos
- Busca de contatos dentro do grupo
- Envio em massa
- Envio individual
- Personalização com `{nome}`
- Suporte a HTML no corpo do e-mail
- Anexos
- Imagem inline/banner
- Botão de WhatsApp no e-mail
- Templates de mensagem
- Histórico de envios
- Exportação do histórico em CSV
- Agendamento de envio
- Barra de progresso
- Interface gráfica com Tkinter + ttkbootstrap

## Tecnologias

- Python
- Tkinter
- ttkbootstrap
- SMTP Gmail
- JSON
- Cryptography/Fernet
- Pillow
- tkhtmlview

## Instalação

Clone o repositório:

```bash
git clone https://github.com/SEU_USUARIO/python-email-bot.git
cd python-email-bot
```

Crie e ative um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute:

```bash
python bot.py
```

## Como usar

1. Abra o app.
2. Faça login com seu Gmail.
3. Use uma senha de app do Gmail, não sua senha normal.
4. Crie um grupo de contatos.
5. Escreva o assunto e a mensagem.
6. Adicione anexos ou imagem inline, se desejar.
7. Clique em **Enviar Agora** ou agende um horário.

## Segurança

Este projeto gera localmente arquivos como:

```text
chave.key
login_criptografado.bin
data/grupos.json
data/historico.json
data/modelos.json
```

Esses arquivos estão no `.gitignore` e não devem ser enviados ao GitHub.

## Observação sobre Gmail

Para enviar e-mails pelo Gmail, normalmente é necessário ativar a autenticação em duas etapas e gerar uma **Senha de App** na conta Google.

## Estrutura

```text
python-email-bot/
│
├── bot.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── assets/
│   └── .gitkeep
│
├── data/
│   └── .gitkeep
│
└── screenshots/
    └── .gitkeep
```

## Autor

Keven Witteny
