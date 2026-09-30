import streamlit as st
import gspread
import sqlite3
from datetime import datetime



def configurar_banco():
    # --    CONECTA COM O BANCO DE DADOS -- #
    conexao = sqlite3.connect('historico.db')
    cursor = conexao.cursor()
    
    # -- EXECUTA A CRIAÇÃO DO BANCO -- #
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS relatorio_diario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_registro TEXT,
            nome_motorista TEXT,
            valor_pendente REAL
        )
    ''')
    
    # SALVA O BANCO
    conexao.commit()
    conexao.close()

def processarPagamentos (dados_planilha):
        # MESMO SISTEMA DO "RELATORIO.PY"
        
        relatorio = {}
        # -- ATRIBUIÇÃO DOS VALORES DO DOCUMENTO -- #
        for linha in dados_planilha: 
            nome = linha['MOTORISTA']
            status = linha['STATUS']  

            # VALIDADOR DE PENDENTE E CONTAGEM
            if status == '':
                status = 'PENDENTE'

            if status == 'PENDENTE':
                texto_valor = str(linha['TOTAL.'])
                texto_adiantamento = str(linha['ADIANTAMENTO'])
                if texto_adiantamento == '':
                    adiantamento_formatado = 0.0
                else:
                    adiantamento_formatado = float(texto_adiantamento.replace(',', '.'))

                if texto_valor == '':
                    valorFormatado = 0.0
                else: 
                    valorFormatado = float(texto_valor.replace(',', '.'))

                valor_liquido = valorFormatado - adiantamento_formatado
                if nome not in relatorio:
                    relatorio[nome] = valor_liquido
                else:
                    relatorio[nome] += valor_liquido

        return relatorio

def conectarPlanilha ():
    # -- CONEXÃO COM O GOOGLE SHEETS -- #
    conta = gspread.service_account(filename='credenciais.json')
    planilha = conta.open('PAGAMENTO MOTORISTA 2026 - V2')
    aba = planilha.worksheet('BANCO')

    # -- PEGA OS DADOS E CHAMA AS FUNÇÕES -- #
    dados_planilha = aba.get_all_records(head=2, value_render_option='UNFORMATTED_VALUE')
    relatorio_final = processarPagamentos(dados_planilha)
    gerarRelatorio(relatorio_final)

def gerarRelatorio(relatorio_final):  
    # -- CONECTA O BANCO E PEGA A DATA -- #
    conexao = sqlite3.connect('historico.db')
    cursor = conexao.cursor()
    data = datetime.now().strftime('%Y-%m-%d')

    relatorio_formatado = []

    # -- EXECUTA PARA CADA MOTORISTA -- #
    for nome, valor in relatorio_final.items():

        if valor != 0.0:
            valor_brl = f"{valor:.2f}".replace(".", ",")
            relatorio_formatado.append({'MOTORISTA': nome, 'VALOR': valor_brl })
            
            # -- INSERE OS VALORES DE CADA REGISTRO NO BANCO
            cursor.execute('''
                INSERT INTO relatorio_diario (data_registro, nome_motorista, valor_pendente)
                VALUES (?, ?, ?) 
            
            ''', (data, nome, valor)) # substitui os "?" dentro do execute

    # -- FECHA O BANCO E GERA A TABELA STREAMLIT -- #
    conexao.commit()
    conexao.close()
    st.dataframe(relatorio_formatado)

    
configurar_banco()

st.title('DASHBOARD :violet[MA2]')
st.subheader('Confira o relatório dos valores faltantes a serem pagos!')
st.write('Abaixo você verá as informações puxadas diretamente do BANCO DE DADOS. Você verá a diferença entre :red[valores pendentes]  e  :green[adiantamentos]')


conectarPlanilha()




