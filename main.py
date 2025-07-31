from libs.lib import *

blocked_ips = set()

if __name__ == "__main__":
    try:
        for line in read_auth_logs():
            # Se identificar que possui o protocolo SSH na entrada
            if identify_protocol(line) == "ssh":
                ssh_connection = get_ssh_connection_details(line,blocked_ips)
            else:
                sudo_details = get_sudo_details(line)
    except KeyboardInterrupt:
        print("\nLista de IPs bloqueados durante a execução:")
        for ip in blocked_ips:
            print(f" - {ip}")
        print("Se quiser desbloquear, execute: sudo ufw delete deny from <endereco_ip> to any")

