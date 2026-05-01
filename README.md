# Tutor IA diário — Prova de Título ABP

Orquestrador diário que roda via GitHub Actions, lê o desempenho do aluno do app principal (via Supabase), chama a API do POE para gerar um pacote de estudos (texto + flashcards), e entrega via bot no Telegram.

## 🤖 Como criar e configurar o Bot do Telegram

Para que o orquestrador te envie mensagens todos os dias às 06:30, você precisa de um Bot.

1. Abra o Telegram e busque por `@BotFather`.
2. Mande o comando `/newbot`.
3. Siga as instruções: dê um nome (ex: `Tutor ABP`) e um username (terminando em `bot`, ex: `MeuTutorABPbot`).
4. O BotFather vai te dar um **Token de Acesso** (algo como `123456789:ABCDefgh...`). Copie e guarde-o (é o `TELEGRAM_BOT_TOKEN`).
5. Agora, **inicie uma conversa com seu novo bot**. Mande um "Oi" para ele.
6. Em seguida, descubra o seu Chat ID acessando no navegador: `https://api.telegram.org/bot<SEU_TOKEN_AQUI>/getUpdates`
7. Procure por `"chat":{"id": 123456789}` no retorno JSON. Esse número é o seu `TELEGRAM_CHAT_ID`.

---

## ☁️ Como configurar o Banco (Supabase)

Como o orquestrador não tem banco de dados próprio, usamos o seu Supabase existente para guardar o estado dos envios (para não mandar repetido).

1. Abra o **SQL Editor** no painel do Supabase.
2. Copie o conteúdo do arquivo `migrations/001_create_tutor_tables.sql` e execute lá. Isso criará as 3 tabelas necessárias (`tutor_daily_plan`, `tutor_daily_compliance`, `tutor_run_log`).

---

## 🚀 Como rodar localmente (para testar)

1. Requer Python 3.11+.
2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # no Windows: venv\Scripts\activate
   ```
3. Instale o pacote:
   ```bash
   pip install -e .
   ```
4. Copie o `.env.example` para `.env` e preencha as chaves:
   - `POE_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`.
5. Teste o fluxo **sem enviar nada** (apenas imprime no console):
   ```bash
   python -m abp_tutor.orchestrator --dry-run
   ```
6. Teste o envio real:
   ```bash
   python -m abp_tutor.orchestrator
   ```

*(Dica: se quiser testar o envio de um dia do passado que já foi gerado, use: `python -m abp_tutor.orchestrator --resend 2026-05-01`)*

---

## ⚙️ Como colocar no GitHub Actions (Automático)

1. Suba este repositório para o seu GitHub (pode ser privado).
2. Vá em **Settings > Secrets and variables > Actions**.
3. Em **Repository secrets**, adicione:
   - `POE_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
4. Em **Repository variables**, adicione:
   - `EXAM_DATE` (ex: `2026-05-30`)
   - `START_DATE` (ex: `2026-05-01`)
5. Vá na aba **Actions** e você pode rodar o "Daily Tutor Run" manualmente clicando em "Run workflow", ou esperar ele rodar automaticamente às 06:30 da manhã do Brasil.
