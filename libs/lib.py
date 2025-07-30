from threading import Thread
from time import sleep
import telebot
import logging
from datetime import datetime
from os import getenv
import requests
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logging.basicConfig(filename='logs/conexoes.log', level=logging.INFO)
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)

def get_chat_id(bot_token, verbose=False):
    """Obtém o chat_id automaticamente usando o bot_token"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url).json()

        if response.get('ok') and response.get('result'):
            chat_id = response['result'][0]['message']['chat']['id']
            print_verbose(f"Chat ID encontrado: {chat_id}", verbose)
            return str(chat_id)
        else:
            print_verbose("Nenhuma atualização encontrada. Envie uma mensagem para o bot primeiro.", verbose)
            return None
    except Exception as e:
        print_verbose(f"Erro ao obter chat_id: {e}", verbose)
        return None

def print_verbose(message, verbose=True):
    """Exibe mensagens no console se verbose=True"""
    if verbose:
        print(f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] {message}")
    logger.info(message)

def send_telegram_message(message: str, verbose: bool = False):
    """Envia mensagem via Telegram apenas se o Vandor estiver online"""
    BOT_TOKEN = getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        msg = "Token do bot não configurado no .env"
        print_verbose(msg, verbose)
        logger.warning(msg)
        return

    CHAT_ID = get_chat_id(BOT_TOKEN, verbose)
    if not CHAT_ID:
        msg = "Não foi possível obter o chat_id"
        print_verbose(msg, verbose)
        logger.warning(msg)
        return
    bot = telebot.TeleBot(BOT_TOKEN)
    try:
        print_verbose("Enviando mensagem via Telegram...", verbose)
        bot.send_message(CHAT_ID, message)
        msg = f"Mensagem enviada no Telegram: {message}"
        print_verbose(msg, verbose)
        logger.info(msg)
    except Exception as e:
        msg = f"Erro ao enviar mensagem no Telegram: {e}"
        print_verbose(msg, verbose)
        logger.error(msg)

# Esta função lê uma linha e identifica o procotolo
def identify_protocol(line : str) -> str:
    if "ssh" in line:
        return "ssh"
    return "sudo"

# Esta função devolve um onjeto com os detalhes de tentativa de escalação de privilégio via sudo
def get_sudo_details(line : str) -> dict:
     
    arr = line.split()
    date = datetime.fromisoformat(arr[0])
    conexao = {
            "username" : "",
            "date" : date.strftime('%-d/%-m/%Y as %H:%M'),
            "attempt" : 0
    }

    # Captura a tentativa falhada do sudo
    if "pam_unix(sudo:auth):" in line:
        username = arr[10].split('=')[1]
        conexao["username"] = username
        log_string = f'Usuário {conexao["username"]} tentou obter privilégios de root em {conexao["date"]}'
        logger.error(log_string)
        print('[ERRO] '+log_string)
        Thread(target=send_telegram_message, args=(log_string,)).start()
    
    # Captura o comando sudo su para abrir sessão do root 
    elif "USER=root ; COMMAND=/usr/bin/su" in line:
        username = arr[3]
        conexao["username"] = username
        log_string = f'Usuário {conexao["username"]} está atualmente logado como ROOT em {conexao["date"]}'
        logger.warning(log_string)
        print('[WARNING] '+log_string)
        Thread(target=send_telegram_message, args=(log_string,)).start()
    

    # Captura a mudança de senha 
    elif "passwd:chauthtok" in line:
        username = arr[7]
        conexao["username"] = username
        log_string = f'A senha do usário {conexao["username"]} foi alterada em {conexao["date"]}'
        logger.warning(log_string)
        print('[WARNING] '+log_string)
        Thread(target=send_telegram_message, args=(log_string,)).start()

    return conexao




# Esta função devolve um objeto com os detalhes de uma conexão SSH recebida
def get_ssh_connection_details(line : str,blocked_ips : set = None) -> dict:
    
    arr = line.split()
    date = datetime.fromisoformat(arr[0])
    conexao = {
            "username" : "",
            "date" : date.strftime('%-d/%-m/%Y as %H:%M'),
            "ip_address" : "",
            "attempt" : 0
    }

    # SSH feito via usuário:senha
    if "Accepted password for" in line:
        username = arr[arr.index('for') + 1]
        ip_address = arr[arr.index('from') + 1]
        conexao["username"] = username
        conexao["ip_address"] = ip_address
        log_string = f'Usuário {conexao["username"]} conectado via SSH pelo endereço IP {conexao["ip_address"]} em {conexao["date"]}'
        logger.info(log_string)
        print('[INFO] '+log_string)
        Thread(target=send_telegram_message, args=(log_string,)).start()
        return conexao

    # Se o usuário fizer 3 tentativas, será bloqueado
    elif "more authentication failures;" in line:
        try:
            parts = {k:v for k,v in [item.split('=') for item in arr if '=' in item]} 
            conexao.update({
                "username": parts.get("user", ""),
                "ip_address": parts.get("rhost", ""),
                "attempt": 3
            })
            
            log_string = f'Registradas {conexao["attempt"]} tentativas do usuário {conexao["username"]} pelo endereço IP {conexao["ip_address"]} em {conexao["date"]}'
            logger.error(log_string)
            send_telegram_message(log_string)
            Thread(target=send_telegram_message, args=(log_string,)).start()
            print('[ERRO] ' + log_string)
            return conexao
            
        except (ValueError, IndexError, KeyError) as e:
            logger.error(f"Erro ao realizar a conversão dos logs: {line} - Error: {str(e)}")
            return None


# Esta função realiza a leitura do arquivo de log
def read_auth_logs():
    with open("/var/log/auth.log","r") as file:
        file.seek(0,2)
        while True:
            linha = file.readline()
            if not linha:
                sleep(1)
                continue
            yield linha


