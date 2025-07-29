from time import sleep
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(filename='logs/conexoes.log', level=logging.INFO)

APP_LOG_FILENAME = 'conexoes.log'

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
        #return conexao
    
    # Captura o comando sudo su para abrir sessão do root 
    elif "USER=root ; COMMAND=/usr/bin/su" in line:
        username = arr[3]
        conexao["username"] = username
        log_string = f'Usuário {conexao["username"]} está atualmente logado como ROOT em {conexao["date"]}'
        logger.warning(log_string)
        print('[WARNING] '+log_string)
        #return conexao

    # Captura a mudança de senha 
    elif "passwd:chauthtok" in line:
        username = arr[7]
        conexao["username"] = username
        log_string = f'A senha do usário {conexao["username"]} foi alterada em {conexao["date"]}'
        logger.warning(log_string)
        print('[WARNING] '+log_string)
        #return conexao

    return conexao




# Esta função devolve um objeto com os detalhes de uma conexão SSH recebida
def get_ssh_connection_details(line : str) -> dict:
    
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

