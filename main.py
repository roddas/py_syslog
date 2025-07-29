from libs.lib import *

if __name__ == "__main__":
    for line in read_auth_logs():
        # Se identificar que possui o protocolo SSH na entrada
        if identify_protocol(line) == "ssh":
            ssh_connection = get_ssh_connection_details(line)
        else:
            sudo_details = get_sudo_details(line)
