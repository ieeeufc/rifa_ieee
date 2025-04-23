import os
import streamlit as st
import tempfile
from PIL import Image
import time
import uuid
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account

def salvar_comprovante(arquivo_imagem):
    """
    Salva o arquivo de comprovante no Google Drive, em uma pasta específica.

    Args:
        arquivo_imagem: Arquivo de imagem do comprovante

    Returns:
        str: URL para a imagem salva no Google Drive
    """

    # Gera um identificador único para o arquivo
    nome_arquivo = f"Comprovante_rifa_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"

    # Caminho para o arquivo de credenciais
    credentials_path = os.environ.get("GOOGLE_CREDENTIALS",
                                 os.path.join(BASE_DIR, "credentials.json"))

    # ID da pasta de destino no Google Drive
    pasta_id = "1w3xYpOX3ootL4jmm0_lQk7LjSvAkAras"

    try:
        # Configurar as credenciais
        SCOPES = ['https://www.googleapis.com/auth/drive']
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES
        )

        # Criar serviço do Drive
        drive_service = build('drive', 'v3', credentials=credentials)

        # Preparar arquivo para upload
        bytes_data = io.BytesIO(arquivo_imagem.getvalue())
        media = MediaIoBaseUpload(bytes_data, mimetype=arquivo_imagem.type)

        # Metadados incluindo o ID da pasta
        file_metadata = {
            'name': nome_arquivo,
            'mimeType': arquivo_imagem.type,
            'parents': [pasta_id]  # Define a pasta de destino
        }

        # Executar o upload
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,webViewLink'
        ).execute()

        # Obter o link para o arquivo no Google Drive
        drive_link = file.get('webViewLink', "")

        return drive_link

    except Exception as e:
        st.error(f"Erro ao salvar comprovante no Google Drive: {str(e)}")
        # Fallback para URL simulada em caso de falha
        return f"https://drive.google.com/drive/u/4/folders/{pasta_id}/{nome_arquivo}"

def validar_numero_contato(contato):
    """
    Valida o formato do número de contato.
    
    Args:
        contato: Número de contato a ser validado
        
    Returns:
        bool: True se for válido, False caso contrário
    """
    # Remove caracteres não numéricos
    contato_limpo = ''.join(filter(str.isdigit, contato))
    
    # Verifica se o número tem entre 10 e 11 dígitos (com ou sem DDD)
    return 10 <= len(contato_limpo) <= 11