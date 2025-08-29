import time
import os
import argparse
from datetime import datetime
from dotenv import load_dotenv
from Util.db_integracao import conectar_banco, obter_cnpj_fundo, deletar_dados_existentes, inserir_dados
from Util.service import obter_token, obter_extrato, limpar_pasta
from Util.processa_relatorios import normalize_df, tratar_colunas, mapear_ids_conta
from Util.auxiliar import preencher_args_com_input, gerar_datas, filtrar_por_datas_existentes, normalizar_date

DAYS_AGO_DEFAULT = 1

def main():
    tempo_inicial = time.time()

    # Parser de argumentos
    parser = argparse.ArgumentParser(description='Script com leitura e validação de datas')
    parser.add_argument('--data', type=lambda s: datetime.strptime(s, '%Y-%m-%d'))
    parser.add_argument('--data-inicial', type=lambda s: datetime.strptime(s, '%Y-%m-%d'))
    parser.add_argument('--data-final', type=lambda s: datetime.strptime(s, '%Y-%m-%d'))
    parser.add_argument('--days-ago', type=int)
    args = parser.parse_args()

    # Completa os argumentos com inputs se necessário
    preencher_args_com_input(args, DAYS_AGO_DEFAULT)

    # Normaliza datas
    data_arg = normalizar_date(args.data) if args.data else None
    data_inicial_arg = normalizar_date(args.data_inicial) if args.data_inicial else None
    data_final_arg = normalizar_date(args.data_final) if args.data_final else None

    # Carrega variáveis de ambiente
    load_dotenv()
    token = os.getenv('VORTX_TOKEN')
    login = os.getenv('VORTX_LOGIN')
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASS')

    conexao = conectar_banco(server, database, username, password)
    if not conexao:
        print('Erro ao conectar ao banco.')
        return

    try:
        # Gera e filtra datas
        datas_candidatas = gerar_datas(data_arg, data_inicial_arg, data_final_arg, args.days_ago)
        datas_validas = filtrar_por_datas_existentes(conexao, datas_candidatas)

        print('\nResumo das datas:')
        print('Candidatas:', [d.strftime('%Y-%m-%d') for d in datas_candidatas])
        print('Válidas no banco:', [d.strftime('%Y-%m-%d') for d in datas_validas])
        print()

        # Verifica se há datas válidas
        if not datas_validas:
            print('Nenhuma Data_Posicao válida encontrada. Abortando.')
            return

        # Token de acesso
        access_token = obter_token(token, login)
        if not access_token:
            print('Falha ao obter token de acesso.')
            return

        cnpjs_convencionais = obter_cnpj_fundo(conexao)
        pasta_saida = './Temp_file/'
        caminho_base = os.path.join(pasta_saida, 'extrato.json')

        limpar_pasta(pasta_saida)

        # Processamento por data
        for d in datas_validas:
            data_posicao_str = d.strftime('%Y-%m-%d')
            print(f'\nProcessando extrato para {data_posicao_str}')
            obter_extrato(access_token, caminho_base, cnpjs_convencionais, data_posicao_str)

            df, nomes_fundos = normalize_df(str(pasta_saida))
            if df.empty or 'ID_CNPJ_Fundo' not in df.columns:
                print('DataFrame está vazio. Nenhum dado foi inserido.')
                continue

            mapa_ids_cota = mapear_ids_conta(conexao, nomes_fundos)
            df = tratar_colunas(df, mapa_ids_cota)

            nome_tabela = 'EXTRATO.Movimento_Conta'
            data_posicao_df = df['Data_Posicao'].iloc[0]

            for cnpj in df['ID_CNPJ_Fundo'].unique():
                deletar_dados_existentes(conexao, data_posicao_df, nome_tabela, cnpj)

            inserir_dados(conexao, nome_tabela, df)

    finally:
        conexao.close()
        print('Conexão com banco encerrada.')
        tempo_final = time.time()
        print(f'\nTempo total de execução: {tempo_final - tempo_inicial:.2f} segundos')

if __name__ == '__main__':
    main()