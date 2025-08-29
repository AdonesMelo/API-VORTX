import requests
import json
import os
import glob

def obter_token(token, login):
    '''
    Obtém um token de autenticação da API da Vortx.

    Retorno:
        str: O token de autenticação se a solicitação for bem-sucedida, caso contrário, None.
    '''
    
    url = 'https://apis.vortx.com.br/vxlogin/api/user/AuthUserApi'

    # Dados para solicitação do token
    payload = {
        'token': token,
        'login': login
        }
    
    headers = {
        'Content-Type': 'application/json'
        }
    
    # Faz a solicitação POST para obter o token
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f'Token obtido com sucesso!')
        return response.json().get('token')
    else:
        print(f'Erro ao autenticar: {response.status_code}, {response.text}')
        return None
    
    
    
def obter_extrato(access_token, caminho_arquivo, cnpjs_convencionais, data_posicao_db):
    '''
    Obtém extratos financeiros para uma lista de CNPJs usando a API da Vortx
    e salva cada extrato em um arquivo JSON separado.

    Entrada:
        access_token (str): O token de acesso para autenticação na API.
        caminho_arquivo (str): O caminho base para salvar os arquivos JSON.
                               O nome do arquivo será gerado com base no CNPJ.
    '''

    url = "https://apis.vortx.com.br/frontier/graphql"

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    for cnpj in cnpjs_convencionais:
        payload = {
            'query': '''
                query GetDemonstrativoCaixa($cnpjFundo: String!, $data: Date!) {
                    getDemonstrativoCaixa(cnpjFundo: $cnpjFundo, data: $data) {
                        entradas {
                            titulo
                            tituloCp
                            data
                            historico
                            tipo
                            debito
                            credito
                            saldo
                            isDetalheTotal
                        }
                        carteira
                        nomeDoFundo
                        dataInicio
                        dataFim
                    }
                }
            ''',
            'variables': {
                'data': str(data_posicao_db),
                'cnpjFundo': str(cnpj)
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                nome_arquivo = os.path.join(
                    os.path.dirname(caminho_arquivo),
                    f'extrato_{cnpj.replace("/", "").replace(".", "").replace("-", "")}.json'
                )
                with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
                    json.dump(response.json(), arquivo, indent=2, ensure_ascii=False)
                print(f'Extrato salvo para {cnpj}')
            else:
                print(f'Erro ao consultar {cnpj}: {response.status_code} - {response.text}')
        except requests.Timeout:
            print(f'Não foi possível buscar demonstrativo de caixa para o CNPJ {cnpj} nessa data {data_posicao_db}.')
            continue
        except requests.RequestException as e:
            print(f'Erro de comunicação ao consultar {cnpj}: {e}')
            continue

def limpar_pasta(diretorio):
    '''
    Limpa o diretório especificado, removendo todos os arquivos dentro dele.
    Se o diretório não existir, ele será criado.
    '''
    if os.path.isdir(diretorio):
        for arquivo in glob.glob(os.path.join(diretorio, '*')):
            os.remove(arquivo)
    else:
        os.makedirs(diretorio, exist_ok=True)