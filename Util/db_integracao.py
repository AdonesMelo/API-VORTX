import pyodbc

def conectar_banco(server, database, username, password):
    '''
    Conecta ao banco de dados SQL Server.
    return: conexão pyodbc ativa ou None em caso de erro
    '''
    try:
        conexao_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};DATABASE={database};UID={username};PWD={password}'
        )
        conexao = pyodbc.connect(conexao_str)
        print('\nConexão com o banco realizada!')
        return conexao
    except pyodbc.Error as e:
        print(f'Erro na conexão com o banco: {e}')
        return None
    
def executar_query(conexao, query, params=None):
    try:
        with conexao.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            resultados = cursor.fetchall()
            return resultados
    except Exception as e:
        print(f'Erro ao executar a query: {e}')
        return None

def obter_cnpj_fundo(conexao):
    '''Obtém a lista de CNPJs dos fundos do banco de dados.'''
    try:
        query = '''
                SELECT f.[ID_Fundo_VORTX]
                ,f.[Nome_Fundo]
                ,f.[ID_CNPJ_Fundo]
                ,f.[Data_criacao]
                ,f.[ID_Status]
                ,fun.[Pasta_Carteira_Padrao]
                ,replace(tp.Tipo_Fundo_Abreviado+' '+fun.Nome_Fundo+'_-_DEMONSTRATIVO_CAIXA_-_[AAAAMMDD]_-_VORTX.json', ' ', '_') padrao_nome_arquivo
                ,cn.Nomenclatura_Carteira Codigo_Carteira
        FROM [ISYS].[ApiVORTX].[FundosVORTX] f
        INNER JOIN [ISYS].[Cadastro].[Fundo] fun ON f.ID_CNPJ_Fundo = fun.ID_CNPJ_Fundo
        INNER JOIN [ISYS].[Parametro].[Tipo_Fundo] tp on fun.ID_Tipo_Fundo = tp.ID_Tipo_Fundo
        INNER JOIN [ISYS].[Cadastro].[Fundo] f2 ON f.ID_CNPJ_Fundo = f2.ID_CNPJ_Fundo
        INNER JOIN [ISYS].[Cota].[Cota_Cadastro] cc on cc.ID_Fundo_Cadastro = f2.ID_Fundo
        INNER JOIN [ISYS].[Cota].[Cota_Nomenclatura] cn on cn.ID_Cota_Cadastro = cc.ID_Cota_Cadastro
        WHERE F.ID_Status = 1 -- Fundo Ativo
        AND f2.Is_Gestao_Solis = 1 -- Gestão Solis
        AND cc.ID_Cota_Tipo = 3 -- Tipo: Cota Subordinada
        AND cn.Conta_Carteira = 'VORTX - CARTEIRA'
        AND cn.ID_Status = 1 -- Cota Nomenclatura Ativa;
        '''
        
        resultados = executar_query(conexao, query)
        cnpjs_convencionais= []
        if resultados:
            for resultado in resultados:
                cnpj_fundo = resultado[2]
                if cnpj_fundo and len(cnpj_fundo) == 14:
                    cnpj_convencional = f'{cnpj_fundo[:2]}.{cnpj_fundo[2:5]}.{cnpj_fundo[5:8]}/{cnpj_fundo[8:12]}-{cnpj_fundo[12:]}'
                    cnpjs_convencionais.append(cnpj_convencional)
                    print(f'CNPJ encontrado: {cnpj_fundo}')
            return cnpjs_convencionais
        else:
            print('Nenhum resultado encontrado.')
            return None
          
    except Exception as e:
        print(f'Erro na manipulação do banco de dados: {e}')
        return None
        
def obter_data_posicao(conexao, data_inicial, data_final):
    '''Retorna lista de datas de posição válidas entre data_inicial e data_final.'''
    query = '''
        SELECT Data_Posicao
        FROM Solis.Data.Data
        WHERE Data_Posicao >= ? AND Data_Posicao <= ?
          AND ID_Status_Dia = 1;
    '''
    resultados = executar_query(conexao, query, [data_inicial, data_final])
    if resultados:
        data_posicoes = [resultado[0].strftime("%Y-%m-%d") for resultado in resultados]
        return data_posicoes
    else:
        print('Nenhuma data de posição encontrada.')
        return []

def obter_id_cota_cadastro(conexao, nome_fundo):
    '''Obtém o ID_Cota_Cadastro para o fundo pelo nome.'''
    try:
        query = '''
            SELECT ID_Cota_Cadastro FROM isys.cota.Cota_Nomenclatura
            WHERE Nomenclatura_Carteira = ?
            AND CNPJ_Administrador = '22610500000188';
        '''
        resultados = executar_query(conexao, query, [nome_fundo])
        if resultados:
            return str(resultados[0][0])
        else:
            print('\nID_Cota_Cadastro: Nenhum resultado encontrado ou erro na consulta.\n')
            return None
    except Exception as e:
        print(f'Erro na manipulação do banco de dados: {e}')
        return None
    
def deletar_dados_existentes(conexao, data_posicao, nome_tabela, cnpj):
    '''Deleta dados existentes na tabela para a data de posição e CNPJ especificados.'''
    try:
        # Verifica se existem dados para deletar
        verifica_query = f'''
            SELECT COUNT(*) FROM {nome_tabela}
            WHERE Data_Posicao = ? AND ID_CNPJ_Fundo = ?;
        '''
        cursor = conexao.cursor()
        cursor.execute(verifica_query, [data_posicao, cnpj])
        count = cursor.fetchone()[0]

        if count > 0:
            delete_query = f'''
                DELETE FROM {nome_tabela}
                WHERE Data_Posicao = ? AND ID_CNPJ_Fundo = ?;
            '''
            cursor.execute(delete_query, [data_posicao, cnpj])
            conexao.commit()
            print(f'{count} registro(s) removido(s) da tabela {nome_tabela} para o CNPJ {cnpj} na data {data_posicao} e os dados reinserido(s) com sucesso.')
        else:
            print(f'Nenhum dado encontrado para {cnpj} na data {data_posicao}. Nada foi deletado.')

        cursor.close()
        return True

    except Exception as e:
        print(f'Erro ao deletar dados existentes: {e}')
        return False

def inserir_dados(conexao, nome_tabela, df):
    '''Insere os dados tratados na tabela do banco de dados.'''
    try:
        # Verificação do DataFrame
        if df.empty:
            print('DataFrame está vazio. Nenhum dado foi inserido.')
            return

        # Preparação da query
        cursor = conexao.cursor()
        colunas = ', '.join(df.columns)
        valores = ', '.join(['?' for _ in df.columns])
        query = f'INSERT INTO {nome_tabela} ({colunas}) VALUES ({valores})'

        with conexao.cursor() as cursor:
            cursor.executemany(query, df.itertuples(index=False, name=None))
            conexao.commit()
        print(f'\nDados inseridos na tabela {nome_tabela} para data posição {df["Data_Posicao"].iloc[0]} com sucesso.')
    except Exception as e:
        print(f'Erro ao inserir dados: {e}')