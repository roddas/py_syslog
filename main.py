from time import sleep 

def abrir_log():
    with open("/var/log/auth.log","r") as file:
        file.seek(0,2)
        while True:
            linha = file.readline()
            if not linha:
                sleep(1)
                continue
            print(linha)

linhas = abrir_log()
#for x in linhas:
#    print(x)
