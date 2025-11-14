import os
import stat
import time
import ctypes
from datetime import datetime
import pikepdf


arquivo = "QA-2022-063.00 - ACORDO DE QUALIDADE MYLAN LABORATORIES.pdf"
nova_data_criacao = datetime(2022, 11, 30, 14, 0, 0)
novo_acesso = time.mktime((2022, 11, 30, 14, 0, 0, 0, 0, -1))  # 13/11/2024 10:00
nova_modificacao = time.mktime((2022, 11, 30, 14, 0, 0, 0, 0, -1))  # 13/11/2024 12:00


def altera_datas(arquivo, nova_data_criacao, novo_acesso, nova_modificacao):
    if novo_acesso is not None and nova_modificacao is not None:
        # Definir timestamps (em segundos desde epoch)
        os.utime(arquivo, (novo_acesso, nova_modificacao))
    
    if nova_data_criacao is not None:
         # Converter para FILETIME
        timestamp = int(nova_data_criacao.timestamp() * 10**7) + 116444736000000000
        handle = ctypes.windll.kernel32.CreateFileW(arquivo, 256, 0, None, 3, 128, None)
        ctypes.windll.kernel32.SetFileTime(handle, ctypes.byref(ctypes.c_longlong(timestamp)), None, None)
        ctypes.windll.kernel32.CloseHandle(handle)


def altera_data_pdf(arquivo, nova_data_criacao):
    if nova_data_criacao is not None:    
        pdf = pikepdf.Pdf.open(arquivo, allow_overwriting_input=True)

        # Formato PDF para datas: D:YYYYMMDDHHmmSS
        data_pdf = "D:" + nova_data_criacao.strftime("%Y%m%d%H%M%S")

        # Alterar metadados
        pdf.docinfo["/CreationDate"] = data_pdf
        pdf.docinfo["/ModDate"] = data_pdf

        # Salvar alterações
        pdf.save(arquivo)
        pdf.close()


def read_only(arquivo, read_only=True):
    if read_only:
        # Tornar o arquivo somente leitura
        os.chmod(arquivo, stat.S_IREAD)
    else:
        # Tornar o arquivo gravável
        os.chmod(arquivo, stat.S_IWRITE)


read_only(arquivo, read_only=False)
#altera_datas(arquivo, nova_data_criacao, novo_acesso, nova_modificacao)
altera_data_pdf(arquivo, nova_data_criacao)
read_only(arquivo, read_only=True)
print("Operação concluída.")
