import pandas as pd
import yfinance as yf
from datetime import timedelta

# =========================================================
# 1. Lendo o CSV de decisões do COPOM
# =========================================================
df_copom = pd.read_csv("copom decisoes 2020 2025.csv")
df_copom['data_decisao'] = pd.to_datetime(df_copom['data_decisao'])
df_copom = df_copom.sort_values('data_decisao').reset_index(drop=True)

# Calcula a direção real do movimento (corte / alta / manutenção)
# comparando a Selic decidida nesta reunião com a da reunião anterior
df_copom['selic_anterior'] = df_copom['selic_nova'].shift(1)

def classifica_direcao(row):
    if pd.isna(row['selic_anterior']):
        return "primeira_reuniao"
    if row['selic_nova'] > row['selic_anterior']:
        return "alta"
    elif row['selic_nova'] < row['selic_anterior']:
        return "corte"
    else:
        return "manutencao"

df_copom['direcao'] = df_copom.apply(classifica_direcao, axis=1)

eventos_completos = df_copom

# =========================================================
# 2. Lista de ativos por setor
# =========================================================
lista_ativos = [
    # Bancos
    "ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "BPAC11.SA", "SANB11.SA",
    # Varejo/Serviços
    "NTCO3.SA", "MGLU3.SA", "LREN3.SA", "RADL3.SA", "CEAB3.SA", "SMFT3.SA", "IGTI11.SA", "AMER3.SA",
    # Commodities/Infra
    "PETR4.SA", "VALE3.SA", "JBSS3.SA", "SBSP3.SA",
    # Construção
    "MRVE3.SA", "CYRE3.SA", "EZTC3.SA",
    # Telecom
    "VIVT3.SA", "TIMS3.SA",
    # Turismo/Aviação
    "CVCB3.SA", "AZUL4.SA",
    # Seguros/Financeiro
    "BBSE3.SA", "B3SA3.SA"
]

# =========================================================
# 3. Função que pega o preço de fechamento em T-1 e T+1
# =========================================================
def preco_t_menos1_t_mais1(ticker, data_evento, janela_busca=10):
    """
    Busca uma janela ampla de pregões ao redor da reunião e retorna:
    - preco_t_menos1: fechamento do último pregão ANTES da data do evento
    - preco_t_mais1: fechamento do primeiro pregão DEPOIS da data do evento
    - data_t_menos1, data_t_mais1: as datas reais usadas (pra auditoria)

    Usamos uma janela de busca ampla (ex: 10 dias corridos antes e depois)
    porque feriados/fins de semana podem deslocar os pregões disponíveis.
    """
    inicio_busca = data_evento - timedelta(days=janela_busca)
    fim_busca = data_evento + timedelta(days=janela_busca)

    dados = yf.download(
        ticker,
        start=inicio_busca.strftime('%Y-%m-%d'),
        end=fim_busca.strftime('%Y-%m-%d'),
        progress=False
    )

    if dados.empty:
        return None

    # Normaliza índice de datas (remove timezone se houver)
    dados.index = pd.to_datetime(dados.index).tz_localize(None)

    pregoes_antes = dados[dados.index.date < data_evento.date()]
    pregoes_depois = dados[dados.index.date > data_evento.date()]

    if pregoes_antes.empty or pregoes_depois.empty:
        return None

    # Último pregão antes (T-1) e primeiro pregão depois (T+1)
    linha_t_menos1 = pregoes_antes.iloc[-1]
    linha_t_mais1 = pregoes_depois.iloc[0]

    preco_t_menos1 = float(linha_t_menos1['Close']) if not hasattr(linha_t_menos1['Close'], 'iloc') else float(linha_t_menos1['Close'].iloc[0])
    preco_t_mais1 = float(linha_t_mais1['Close']) if not hasattr(linha_t_mais1['Close'], 'iloc') else float(linha_t_mais1['Close'].iloc[0])

    return {
        'preco_t_menos1': preco_t_menos1,
        'preco_t_mais1': preco_t_mais1,
        'data_t_menos1': pregoes_antes.index[-1].date(),
        'data_t_mais1': pregoes_depois.index[0].date(),
    }


# =========================================================
# 4. Loop principal: gera o dataset de arestas (ação, evento, peso)
# =========================================================
linhas_resultado = []

for ticker in lista_ativos:
    print("\n" + "=" * 60)
    print(f"--- Calculando impacto da Selic no ativo {ticker} (janela T-1 -> T+1) ---")
    print("=" * 60 + "\n")

    for _, row in eventos_completos.iterrows():
        data_evento = row['data_decisao']

        resultado = preco_t_menos1_t_mais1(ticker, data_evento)

        if resultado is None:
            continue

        variacao = ((resultado['preco_t_mais1'] / resultado['preco_t_menos1']) - 1) * 100

        print(f"Reunião: {data_evento.date()} | Selic: {row['selic_anterior']}% -> {row['selic_nova']}% | Direção: {row['direcao']}")
        print(f"  Pregão T-1 ({resultado['data_t_menos1']}): R${resultado['preco_t_menos1']:.2f}")
        print(f"  Pregão T+1 ({resultado['data_t_mais1']}): R${resultado['preco_t_mais1']:.2f}")
        print(f"  Impacto (Peso da Aresta): {variacao:.2f}%\n")

        linhas_resultado.append({
            'ticker': ticker,
            'data_reuniao': data_evento.date(),
            'selic_anterior': row['selic_anterior'],
            'selic_nova': row['selic_nova'],
            'direcao': row['direcao'],
            'data_t_menos1': resultado['data_t_menos1'],
            'preco_t_menos1': resultado['preco_t_menos1'],
            'data_t_mais1': resultado['data_t_mais1'],
            'preco_t_mais1': resultado['preco_t_mais1'],
            'impacto_pct': round(variacao, 4),
        })

# =========================================================
# 5. Salva tudo em CSV (formato "lista de arestas" do grafo bipartido)
# =========================================================
df_resultado = pd.DataFrame(linhas_resultado)
df_resultado.to_csv("arestas_impacto_selic.csv", index=False)
print(f"\nArquivo 'arestas_impacto_selic.csv' salvo com {len(df_resultado)} linhas (arestas).")
