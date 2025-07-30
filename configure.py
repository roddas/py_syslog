import subprocess
from shutil import which
from dotenv import load_dotenv
from os import getenv


# Este script realiza a configuração do programa

def service_exists(service_name: str) -> bool:
    try:
        result = subprocess.run(
            ["systemctl", "status", service_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode in (0, 3)  # 0 = active, 3 = inactive
    except:
        return False

def command_exists(cmd_name: str) ->str:
    return which(cmd_name) is not None

service = "rsyslog"
command_list = ["iptables"]
load_dotenv()

for command in command_list:
    if command_exists(command):
        print(f"{command} OK ...")
    else:
        print(f"[ERRO] {command} não existe. Instale primeiro")

print("Token do Telegram OK" if getenv("BOT_TOKEN") else "[ERRO] é necessário configurar o token do Telegram para o envio de mensagens automáticas .")


if service_exists(service):
    print(f"Serviço {service} funcionando perfeitamente")
else:
    print(f"[ERRO] O serviço rsyslog não existe. Instale primeiro")
