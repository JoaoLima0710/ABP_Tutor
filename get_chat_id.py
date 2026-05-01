import sys
import time

try:
    import httpx
except ImportError:
    print("Erro: A biblioteca 'httpx' não está instalada.")
    print("Execute 'pip install httpx' no seu ambiente e tente novamente.")
    sys.exit(1)

def get_chat_id():
    print("="*60)
    print("🤖 Descobridor de TELEGRAM_CHAT_ID")
    print("="*60)
    print("\n1. Certifique-se de que você já iniciou a conversa com seu bot no Telegram (mandou um 'Oi').")
    
    token = input("2. Cole aqui o seu TELEGRAM_BOT_TOKEN (fornecido pelo BotFather):\n> ").strip()
    
    if not token:
        print("Token inválido.")
        return

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    
    print("\nBuscando as mensagens recentes do seu bot...")
    
    try:
        with httpx.Client() as client:
            resp = client.get(url, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
            
            if not data.get("ok"):
                print(f"Erro na API do Telegram: {data}")
                return
                
            messages = data.get("result", [])
            if not messages:
                print("\n⚠️ Nenhuma mensagem encontrada!")
                print("Por favor, abra o Telegram, mande qualquer mensagem para o seu bot (ex: 'Oi') e rode este script novamente.")
                return
                
            # Pega a mensagem mais recente
            last_msg = messages[-1]
            chat_obj = last_msg.get("message", {}).get("chat", {})
            
            chat_id = chat_obj.get("id")
            first_name = chat_obj.get("first_name", "Usuário")
            
            if chat_id:
                print("\n✅ Sucesso!")
                print(f"Mensagem encontrada de: {first_name}")
                print(f"Seu TELEGRAM_CHAT_ID é: {chat_id}")
                print("\nCopie esse número e coloque na variável TELEGRAM_CHAT_ID do seu Github ou do arquivo .env.")
            else:
                print("\nNão foi possível extrair o chat_id do formato da mensagem.")
                print(last_msg)
                
    except Exception as e:
        print(f"\nErro ao tentar conectar com o Telegram: {e}")

if __name__ == "__main__":
    get_chat_id()
