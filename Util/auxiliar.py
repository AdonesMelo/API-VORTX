from datetime import datetime, timedelta, date
from Util.db_integracao import obter_data_posicao

def normalizar_date(obj):
    ''' Converte um objeto para datetime.date, tratando diferentes tipos de entrada. '''
    if isinstance(obj, date) and not isinstance(obj, datetime):
        return obj
    if isinstance(obj, datetime):
        return obj.date()
    if isinstance(obj, str):
        return datetime.strptime(obj, '%Y-%m-%d').date()
    raise TypeError(f'Tipo de data não suportado: {type(obj)}')

def ajustar_limites_dia(dmin: date, dmax: date):
    ''' Converte datas para datetime, ajustando o início e fim do dia. '''
    inicio = datetime.combine(dmin, datetime.min.time())
    fim = datetime.combine(dmax, datetime.max.time())
    return inicio, fim

def ler_data_input(mensagem):
    ''' Lê uma data do usuário via input, retornando um objeto datetime.date. '''
    valor = input(mensagem).strip()
    if not valor:
        return None
    try:
        return datetime.strptime(valor, '%Y-%m-%d').date()
    except ValueError:
        print(f'Data inválida: {valor}. Use o formato aaaa-mm-dd.')
        return ler_data_input(mensagem)

def preencher_args_com_input(args, DAYS_AGO_DEFAULT):
    ''' Preenche os argumentos com input do usuário se não estiverem definidos. '''
    if args.data is None and args.data_inicial is None and args.data_final is None:
        args.data = ler_data_input('Digite a data específica (aaaa-mm-dd) ou deixe em branco: ')
        if args.data is None:
            args.data_inicial = ler_data_input('Digite a data inicial (aaaa-mm-dd) ou deixe em branco: ')
            if args.data_inicial:
                args.data_final = ler_data_input('Digite a data final (aaaa-mm-dd): ')
                while args.data_final and args.data_final < args.data_inicial:
                    print('Data final não pode ser menor que a inicial.')
                    args.data_final = ler_data_input('Digite novamente a data final (aaaa-mm-dd): ')
            else:
                args.days_ago = DAYS_AGO_DEFAULT
    if args.days_ago is None:
        args.days_ago = DAYS_AGO_DEFAULT

def gerar_datas(data_dt, data_inicial_dt, data_final_dt, days_ago):
    ''' Gera uma lista de datas candidatas com base nos argumentos fornecidos. '''
    if data_dt:
        return [normalizar_date(data_dt)]
    elif data_inicial_dt and data_final_dt:
        di = normalizar_date(data_inicial_dt)
        df = normalizar_date(data_final_dt)
        dias = (df - di).days
        return [di + timedelta(days=i) for i in range(dias + 1)]
    else:
        return [(datetime.today() - timedelta(days=days_ago)).date()]

def filtrar_por_datas_existentes(conexao, datas_candidatas):
    ''' Filtra as datas candidatas para manter apenas aquelas que existem no banco de dados. '''
    if not datas_candidatas:
        return []
    dmin, dmax = min(datas_candidatas), max(datas_candidatas)
    start_dt, end_dt = ajustar_limites_dia(dmin, dmax)
    datas_existentes_raw = obter_data_posicao(conexao, start_dt, end_dt) or []
    datas_existentes = {normalizar_date(d) for d in datas_existentes_raw}
    return sorted([d for d in datas_candidatas if d in datas_existentes])
