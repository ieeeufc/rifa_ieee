import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os

class SheetsManager:
    def __init__(self, credentials_path, spreadsheet_name):
        """
        Inicializa o gerenciador de planilhas do Google Sheets.
        
        Args:
            credentials_path: Caminho para o arquivo de credenciais JSON do Google API
            spreadsheet_name: Nome da planilha do Google Sheets
        """
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
                 
        credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
        client = gspread.authorize(credentials)
        
        self.spreadsheet = client.open(spreadsheet_name)
        self.numeros_worksheet = self.spreadsheet.worksheet("Numeros")
        self.registros_worksheet = self.spreadsheet.worksheet("Registros")
        
        # Verifica se a planilha de números está inicializada, se não, cria
        self._inicializar_planilha_numeros()
        self._inicializar_planilha_registros()
        
    def _inicializar_planilha_numeros(self):
        """Inicializa a planilha de números caso ainda não tenha sido configurada."""
        try:
            valores = self.numeros_worksheet.get_all_values()
            if not valores:
                # Se a planilha estiver vazia, inicializa com 250 números
                celulas = []
                for i in range(1, 251):
                    celulas.append([i, "Disponível"])
                self.numeros_worksheet.update('A1:B250', celulas)
                self.numeros_worksheet.format('A1:B1', {'textFormat': {'bold': True}})
                self.numeros_worksheet.update('A1:B1', [["Número", "Status"]])
        except gspread.exceptions.WorksheetNotFound:
            # Criar worksheet caso não exista
            self.numeros_worksheet = self.spreadsheet.add_worksheet("Numeros", 250, 2)
            self.numeros_worksheet.update('A1:B1', [["Número", "Status"]])
            celulas = []
            for i in range(1, 251):
                celulas.append([i, "Disponível"])
            self.numeros_worksheet.update('A2:B251', celulas)
    
    def _inicializar_planilha_registros(self):
        """Inicializa a planilha de registros caso ainda não tenha sido configurada."""
        try:
            valores = self.registros_worksheet.get_all_values()
            if not valores:
                self.registros_worksheet.update('A1:E1', 
                                             [["ID", "Nome", "Contato", "Números", "Link Comprovante"]])
                self.registros_worksheet.format('A1:E1', {'textFormat': {'bold': True}})
        except gspread.exceptions.WorksheetNotFound:
            # Criar worksheet caso não exista
            self.registros_worksheet = self.spreadsheet.add_worksheet("Registros", 1000, 5)
            self.registros_worksheet.update('A1:E1', 
                                         [["ID", "Nome", "Contato", "Números", "Link Comprovante"]])
            self.registros_worksheet.format('A1:E1', {'textFormat': {'bold': True}})
    
    def obter_numeros_disponiveis(self):
        """Retorna uma lista de números disponíveis para escolha."""
        # Obtém todos os valores da worksheet
        valores = self.numeros_worksheet.get_all_values()
        
        numeros_disponiveis = []
        # Pula o cabeçalho
        for linha in valores[1:]:
            if len(linha) >= 2 and linha[1] == "Disponível":
                try:
                    numeros_disponiveis.append(int(linha[0]))
                except ValueError:
                    pass
                    
        return numeros_disponiveis
    
    def reservar_numeros(self, numeros_selecionados):
        """
        Marca os números selecionados como 'Reservado' na planilha.
        
        Args:
            numeros_selecionados: Lista de números a serem reservados
            
        Returns:
            bool: True se todos os números foram reservados com sucesso
        """
        # Verificar quais números ainda estão disponíveis
        numeros_disponiveis = self.obter_numeros_disponiveis()
        
        # Filtrar apenas os números que realmente estão disponíveis
        numeros_para_reservar = [n for n in numeros_selecionados if n in numeros_disponiveis]
        
        # Se algum número solicitado não está disponível, retorna False
        if len(numeros_para_reservar) != len(numeros_selecionados):
            return False
            
        # Marcar cada número como reservado
        for numero in numeros_para_reservar:
            # A numeração das células no Google Sheets começa em 1
            # Como a primeira linha é o cabeçalho, somamos 1 para obter a linha correta
            row = numero + 1  # +1 para o cabeçalho
            self.numeros_worksheet.update_cell(row, 2, "Reservado")
            
        return True
        
    def registrar_compra(self, nome, contato, numeros_selecionados, comprovante_url):
        """
        Registra uma nova compra na planilha de registros.
        
        Args:
            nome: Nome do comprador
            contato: Número de contato
            numeros_selecionados: Lista de números escolhidos
            comprovante_url: URL para o comprovante de pagamento
            
        Returns:
            int: ID do registro criado
        """
        # Obter o próximo ID de registro (número da última linha + 1)
        try:
            registros = self.registros_worksheet.get_all_values()
            proximo_id = len(registros)  # Este será o índice da nova linha
        except:
            proximo_id = 1  # Se houver erro ou a planilha estiver vazia
        
        # Converter a lista de números para string
        numeros_str = ", ".join(map(str, numeros_selecionados))
        
        # Criar nova linha no registro
        self.registros_worksheet.append_row([proximo_id, nome, contato, numeros_str, comprovante_url])
        
        return proximo_id