import json
import pandas as pd
import os
from Util.db_integracao import obter_id_cota_cadastro

def normalize_df(pasta='./Temp_file'):
    '''
    Lê todos os arquivos JSON da pasta e retorna um DataFrame consolidado.
    '''
    todos_dfs = []
    nomes_fundos = {}

    if not os.path.exists(pasta):
        print(f"Pasta '{pasta}' não encontrada.")
        return pd.DataFrame(), {}

    lista_arquivos = os.listdir(pasta)

    for arquivo in lista_arquivos:
        if arquivo.endswith('.json'):
            caminho = os.path.join(pasta, arquivo)
            with open(caminho, 'r', encoding='utf-8') as file:
                dados = json.load(file)

                # Tratamento para arquivos com "errors"
                if "errors" in dados and dados["errors"]:
                    print(f"{arquivo}: Não foi possível buscar demonstrativo de caixa")
                    continue

                try:
                    entradas = dados['data']['getDemonstrativoCaixa'][0]['entradas']
                    nome_fundo = dados['data']['getDemonstrativoCaixa'][0].get('nomeDoFundo', 'Fundo desconhecido')
                    df = pd.DataFrame(entradas)

                    # Extrai CNPJ do nome do arquivo
                    cnpj = arquivo.replace('extrato_', '').replace('.json', '')
                    df['ID_CNPJ_Fundo'] = cnpj
                    nomes_fundos[cnpj] = nome_fundo
                    todos_dfs.append(df)
                except (KeyError, IndexError, TypeError):
                    print(f"Erro ao processar {arquivo}: estrutura inesperada.")

    df_final = pd.concat(todos_dfs, ignore_index=True) if todos_dfs else pd.DataFrame()
    return df_final, nomes_fundos

def mapear_ids_conta(conexao, nomes_fundos):
    '''Mapeia os IDs de conta com base nos nomes dos fundos.'''
    mapa_ids = {}
    for cnpj, nome_fundo in nomes_fundos.items():
        id_conta = obter_id_cota_cadastro(conexao, nome_fundo)
        mapa_ids[cnpj] = id_conta if id_conta else '0'  # Preenche com '0' se não encontrar
    return mapa_ids

def tratar_colunas(df, id_cota_cadastro):
    '''Trata as colunas do DataFrame para padronização e formatação.'''
    if 'ID_CNPJ_Fundo' not in df.columns:
        print("Coluna 'ID_CNPJ_Fundo' não encontrada no DataFrame.")
        return df  # ou lançar uma exceção, dependendo do fluxo desejado

    # Concatenar valores das colunas e deletar as colunas que não serão utilizadas
    if 'titulo' in df.columns and 'tituloCp' in df.columns:
        df['Observacao'] = df['titulo'] + ' - ' + df['tituloCp']
        df.drop(['titulo', 'tituloCp', 'tipo', 'debito', 'credito', 'isDetalheTotal'], axis=1, inplace=True)
    else:
        df['Observacao'] = ''

    # Criar coluna Contabil com base na coluna saldo
    if 'saldo' in df.columns:
        df['Contabil'] = df['saldo'].apply(lambda x: 'C' if x >= 0 else 'D')
        df['saldo'] = df['saldo'].abs()  # Remove o sinal negativo
    else:
        df['Contabil'] = ''
    
    # Formatar coluna data
    if 'data' in df.columns:
        df['data'] = pd.to_datetime(df['data']).dt.strftime('%Y-%m-%d')
    
    renomear_colunas = {
        'data': 'Data_Posicao', 
        'historico': 'Lancamento', 
        'saldo': 'Valor_Total'
    }

    for coluna in renomear_colunas:
        if coluna not in df.columns:
            df[coluna] = ''
    df.rename(columns=renomear_colunas, inplace=True)
    
    
    df['ID_Cota_Cadastro'] = df['ID_CNPJ_Fundo'].map(id_cota_cadastro)
    df['ID_Cota_Cadastro'] = df['ID_Cota_Cadastro'].astype(int)
    
    df['ID_Transaction'] = 'PYTHON_V1.0'

    # Padronizar texto da coluna 'Lancamento'
    if 'Lancamento' in df.columns:
        df['Lancamento'] = df['Lancamento'].astype(str).str.upper()

    return df