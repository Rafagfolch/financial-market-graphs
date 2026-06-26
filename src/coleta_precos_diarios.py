import pandas as pd
import yfinance as yf


lista_ativos = [
    "ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "BPAC11.SA", "SANB11.SA",
    "MGLU3.SA", "LREN3.SA", "RADL3.SA", "CEAB3.SA", "SMFT3.SA", "IGTI11.SA", "AMER3.SA",
    "PETR4.SA", "VALE3.SA", "SBSP3.SA",
    "MRVE3.SA", "CYRE3.SA", "EZTC3.SA",
    "VIVT3.SA", "TIMS3.SA",
    "CVCB3.SA",
    "BBSE3.SA", "B3SA3.SA"
]

DATA_INICIO = "2020-01-01"
DATA_FIM = "2026-01-01"  
precos_por_ativo = {}

for ticker in lista_ativos:
    print(f"Baixando histórico completo de {ticker}...")
    dados = yf.download(ticker, start=DATA_INICIO, end=DATA_FIM, progress=False)

    if dados.empty:
        print(f"  [aviso] Nenhum dado retornado para {ticker}.")
        continue

    fechamento = dados['Close']
    if hasattr(fechamento, 'iloc') and len(fechamento.shape) > 1:
        fechamento = fechamento.iloc[:, 0]

    fechamento.index = pd.to_datetime(fechamento.index).tz_localize(None)
    precos_por_ativo[ticker] = fechamento
    print(f"  OK: {len(fechamento)} pregões coletados.")


df_precos = pd.DataFrame(precos_por_ativo)
df_precos = df_precos.sort_index()

print(f"\nTabela final: {df_precos.shape[0]} datas x {df_precos.shape[1]} ativos")
print(f"Período: {df_precos.index.min().date()} a {df_precos.index.max().date()}")


df_precos.to_csv("precos_diarios_2020_2025.csv")
df_retornos = df_precos.pct_change().dropna(how='all') * 100


df_retornos.to_csv("retornos_diarios_2020_2025_largo.csv")

df_retornos_long = (
    df_retornos
    .reset_index()
    .rename(columns={'index': 'data', 'Date': 'data'})
    .melt(id_vars='data', var_name='ticker', value_name='retorno')
    .dropna(subset=['retorno'])
    .sort_values(['data', 'ticker'])
    .reset_index(drop=True)
)
df_retornos_long['data'] = pd.to_datetime(df_retornos_long['data']).dt.strftime('%Y-%m-%d')
df_retornos_long.to_csv("retornos_diarios_2020_2025.csv", index=False)

print("\nArquivos salvos:")
print("  precos_diarios_2020_2025.csv          (precos de fechamento brutos, formato largo)")
print("  retornos_diarios_2020_2025_largo.csv  (variacao % diaria, formato largo - p/ inspecao)")
print("  retornos_diarios_2020_2025.csv        (variacao % diaria, formato LONGO - usar este no arvoreGerado.py)")