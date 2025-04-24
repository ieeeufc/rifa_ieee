import os
import streamlit as st
import io
import time
import uuid
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
import json

def salvar_comprovante(arquivo_imagem):
    """
    Salva o arquivo de comprovante no Google Drive, em uma pasta específica.

    Args:
        arquivo_imagem: Arquivo de imagem do comprovante (objeto UploadedFile do Streamlit)

    Returns:
        str: URL para a imagem salva no Google Drive
    """

    nome_arquivo = f"Comprovante_rifa_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
    pasta_id = "1w3xYpOX3ootL4jmm0_lQk7LjSvAkAras"

    try:
        SCOPES = ['https://www.googleapis.com/auth/drive']

        # Tentar carregar credenciais do Streamlit Secrets
        if "gcp_service_account" in st.secrets:
            credentials_info = dict(st.secrets["gcp_service_account"])
            if "private_key" in credentials_info:
                credentials_info["private_key"] = credentials_info["private_key"].replace("\\n", "\n")
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info, scopes=SCOPES)
            st.write("Usando credenciais do Streamlit Secrets")
        else:
            # Fallback para arquivo local
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            credentials_path = os.path.join(BASE_DIR, "credentials.json")
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=SCOPES)
            st.write(f"Usando credenciais do arquivo local: {credentials_path}")

        drive_service = build('drive', 'v3', credentials=credentials)

        # Criar objeto BytesIO para o arquivo
        arquivo_imagem.seek(0)  # Garante que o cursor está no começo
        bytes_data = io.BytesIO(arquivo_imagem.read())

        media = MediaIoBaseUpload(bytes_data, mimetype=arquivo_imagem.type)

        file_metadata = {
            'name': nome_arquivo,
            'mimeType': arquivo_imagem.type,
            'parents': [pasta_id]
        }

        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        drive_link = file.get('webViewLink', "")
        return drive_link

    except Exception as e:
        st.error(f"Erro ao salvar comprovante no Google Drive: {e}")
        return f"https://drive.google.com/drive/u/4/folders/{pasta_id}/{nome_arquivo}"


def validar_numero_contato(contato):
    """
    Valida o formato do número de contato.

    Args:
        contato: Número de contato a ser validado

    Returns:
        bool: True se for válido, False caso contrário
    """
    contato_limpo = ''.join(filter(str.isdigit, contato))
    return 10 <= len(contato_limpo) <= 11
