import streamlit as st
import os
from PIL import Image
import pandas as pd
import io
from sheets_manager import SheetsManager
from utils import salvar_comprovante, validar_numero_contato, carregar_credenciais

def main():
    # Configurações da página
    st.set_page_config(
        page_title="Rifa RNR",
        page_icon="img/CARCARÁ.jpg",  # Isso define o ícone da aba
        layout="wide"
    )

    col1, col2 = st.columns([2, 6])  # Ajuste os valores para balancear largura

    with col1:
        st.image("img/CARCARÁ.jpg", width=80)  # Tamanho ajustável

    with col2:
        st.title("Rifa Reunião Nacional dos Ramos IEEE")
    st.markdown("""
    <div style='font-size:18px; line-height:1.6; margin-top: 10px;'>
        <h2>🎁 Concorra a uma incrível Garrafa Térmica Fresh 950ml da Gocase!</h2><br>
        Escolha seus números da sorte e preencha o formulário abaixo para garantir sua participação.<br>
        ✨ Mantenha suas bebidas geladas com estilo e praticidade — não perca essa chance!
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar o gerenciador de planilhas
    # Em produção, você deve usar st.secrets para armazenar o caminho de credenciais
    spreadsheet_name = 'Sistema de Rifas'
    try:
        # Tenta primeiro usar os secrets (para deploy)
        credentials_info = st.secrets["gcp_service_account"]
        print("Chave privada (primeiros 30 caracteres):", repr(credentials_info["private_key"][:30]))
        
        sheets_manager = SheetsManager(credentials_info=credentials_info, spreadsheet_name=spreadsheet_name)
        numeros_disponiveis = sheets_manager.obter_numeros_disponiveis()

    except Exception as e:
        try:
            # Se falhar, tenta com o arquivo local (para desenvolvimento)
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            credentials_path = os.path.join(BASE_DIR, "credentials.json")
            print("Usando credenciais de arquivo local:", credentials_path)
            
            sheets_manager = SheetsManager(credentials_path=credentials_path, spreadsheet_name=spreadsheet_name)
            numeros_disponiveis = sheets_manager.obter_numeros_disponiveis()
        except Exception as e:
            st.error(f"Erro ao conectar com Google Sheets: {str(e)}")
            st.error("Verifique se o arquivo de credenciais está correto e se a planilha existe.")
            st.stop()
    
    # Exibir números disponíveis
    st.subheader("Números Disponíveis")
    
    # Converter para DataFrame para exibição mais agradável
    df = pd.DataFrame({"Número": numeros_disponiveis})
    
    # Dividir em colunas para melhor visualização
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("Total disponível:", len(numeros_disponiveis))
    
    with col2:
        if len(numeros_disponiveis) > 0:
            st.write("Menor número disponível:", min(numeros_disponiveis))
    
    with col3:
        if len(numeros_disponiveis) > 0:
            st.write("Maior número disponível:", max(numeros_disponiveis))
    
    # Exibir tabela com números disponíveis (formatada em grid)
    if numeros_disponiveis:
        # Criamos uma lista de listas, onde cada lista interna tem 10 elementos
        # para exibir os números em uma grid de 6 colunas
        grid_data = []
        for i in range(0, len(numeros_disponiveis), 6):
            grid_data.append(numeros_disponiveis[i:i+6])
        
        # Criar um DataFrame com as linhas da grid
        grid_df = pd.DataFrame(grid_data)
        
        # Exibir a grid sem o cabeçalho das colunas
        st.dataframe(grid_df, hide_index=True)
    else:
        st.warning("Não há números disponíveis no momento!")
    
    # Formulário para seleção de números
    st.subheader("Escolha seus números da sorte")
    
    with st.form(key="rifa_form"):
        nome = st.text_input("Nome completo")
        contato = st.text_input("Número de contato (WhatsApp)")
        
        # Input para seleção de múltiplos números
        numeros_texto = st.text_input(
            "Números escolhidos (separados por vírgula, ex: 1, 5, 23)", 
            help="Digite os números que deseja escolher separados por vírgula"
        )
        
        # Upload do comprovante
        st.markdown("### Comprovante de Pagamento")
        st.markdown("""
        Faça o PIX para: ieee@email.com
        Valor: R$ 6,00 por número escolhido
        """)
        
        comprovante = st.file_uploader(
            "Envie o comprovante de pagamento (apenas imagens)", 
            type=["png", "jpg", "jpeg"]
        )
        
        # Botão de envio
        submit_button = st.form_submit_button(label="Confirmar participação")
    
    # Processamento do formulário
    if submit_button:
        # Validar nome
        if not nome.strip():
            st.error("Por favor, informe seu nome.")
            st.stop()
        
        # Validar contato
        if not validar_numero_contato(contato):
            st.error("Por favor, informe um número de contato válido.")
            st.stop()
        
        # Validar e processar números escolhidos
        try:
            numeros_escolhidos = [int(num.strip()) for num in numeros_texto.split(",") if num.strip()]
            # Remover duplicatas
            numeros_escolhidos = list(set(numeros_escolhidos))
            
            # Verificar se os números estão entre 1 e 250
            for num in numeros_escolhidos:
                if num < 1 or num > 250:
                    st.error(f"O número {num} está fora do intervalo permitido (1-250).")
                    st.stop()
                
            # Verificar se não foram escolhidos números
            if not numeros_escolhidos:
                st.error("Por favor, escolha pelo menos um número.")
                st.stop()
        except ValueError:
            st.error("Por favor, digite apenas números separados por vírgulas.")
            st.stop()
        
        # Verificar se todos os números escolhidos estão disponíveis
        indisponiveis = [num for num in numeros_escolhidos if num not in numeros_disponiveis]
        if indisponiveis:
            st.error(f"Os seguintes números não estão disponíveis: {', '.join(map(str, indisponiveis))}")
            st.stop()
        
        # Validar comprovante
        if not comprovante:
            st.error("Por favor, envie o comprovante de pagamento.")
            st.stop()
        
        # Tudo validado, processar a solicitação
        try:
            # Salvar comprovante e obter URL
            comprovante_url = salvar_comprovante(comprovante)
            
            # Registrar na planilha de registros
            registro_id = sheets_manager.registrar_compra(nome, contato, numeros_escolhidos, comprovante_url)
            
            # Reservar números
            sucesso = sheets_manager.reservar_numeros(numeros_escolhidos)
            
            if sucesso:
                st.success(f"Parabéns {nome}! Seus números foram reservados com sucesso.")
                st.success(f"Números escolhidos: {', '.join(map(str, numeros_escolhidos))}")
                st.success(f"Seu registro foi confirmado com o ID: {registro_id}")
                
                # Exibir prévia do comprovante
                if comprovante:
                    st.image(comprovante, caption="Comprovante de pagamento", width=300)
                
                # Botão para nova participação
                if st.button("Fazer nova participação"):
                    st.experimental_rerun()
            else:
                st.error("Ocorreu um erro ao reservar os números. Por favor, tente novamente.")
        except Exception as e:
            st.error(f"Ocorreu um erro ao processar sua solicitação: {str(e)}")
    
    # Rodapé
    st.markdown("---")
    st.markdown("© 2025 - Sistema de Rifas - Todos os direitos reservados.")

if __name__ == "__main__":
    main()