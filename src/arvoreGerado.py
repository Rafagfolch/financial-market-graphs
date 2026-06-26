import pandas as pd
import math

REGIMES_SELIC = [
    ("Regime_1", "2020-02-05", "2020-08-05"), 
    ("Regime_2", "2020-09-16", "2021-01-20"),  
    ("Regime_3", "2021-03-17", "2022-08-03"),  
    ("Regime_4", "2022-09-21", "2023-06-21"), 
    ("Regime_5", "2023-08-02", "2024-05-08"), 
    ("Regime_6", "2024-06-19", "2024-07-31"),  
    ("Regime_7", "2024-09-18", "2025-06-18"), 
    ("Regime_8", "2025-07-30", "2025-12-10"), 
]


def atribuir_regime(data):
    data = pd.to_datetime(data)
    for nome, inicio, fim in REGIMES_SELIC:
        if pd.to_datetime(inicio) <= data <= pd.to_datetime(fim):
            return nome
    return None

def calcular_distancias_mantegna(df_regime, col_data, col_val):
    tabela_dinamica = df_regime.pivot_table(index=col_data, columns='ticker', values=col_val)
    tabela_dinamica = tabela_dinamica.dropna(axis=1, how='all')

    matriz_correlacao = tabela_dinamica.corr(method='pearson')
    rotulos = list(matriz_correlacao.columns)
    quantidade_ativos = len(rotulos)

    matriz_dist = []
    for i in range(quantidade_ativos):
        linha = []
        for j in range(quantidade_ativos):
            if i == j:
                linha.append(0.0)
            else:
                correlacao = matriz_correlacao.iloc[i, j]
                if pd.isna(correlacao):
                    correlacao = 0.0
                dist = math.sqrt(2 * (1 - correlacao))
                linha.append(dist)
            linha[-1] = linha[-1]
        matriz_dist.append(linha)

    return matriz_dist, rotulos

def construir_grafo_completo(matriz_dist, rotulos):
    quantidade = len(matriz_dist)
    G = {i: {} for i in range(quantidade)}

    for i in range(quantidade):
        for j in range(quantidade):
            if i != j:
                G[i][j] = matriz_dist[i][j]

    return G

def prim(G):
    vertices = list(G.keys())
    v = vertices[0]
    S = [v]
    N = [x for x in vertices if x != v]
    T = []

    while len(T) < len(vertices) - 1:
        menor_peso = float('inf')
        v1, v2 = None, None

        for i in S:
            for j in N:
                if j in G[i] and G[i][j] < menor_peso:
                    menor_peso = G[i][j]
                    v1, v2 = i, j

        if v2 is None:
            break

        S.append(v2)
        N.remove(v2)
        T.append((v1, v2))

    return T


def converter_para_lista_adjacencia(T, G):
    MST = {}
    for v, u in T:
        peso = G[v][u]
        MST.setdefault(v, {})[u] = peso
        MST.setdefault(u, {})[v] = peso
    return MST


def custo_total(T, G):
    return sum(G[v][u] for v, u in T)


def exportar_arvore(T, G, rotulos, caminho_saida):
    linhas = []
    for v, u in T:
        linhas.append({
            'Origem': rotulos[v],
            'Destino': rotulos[u],
            'Distancia_Mantegna': round(G[v][u], 4)
        })

    df_arestas = pd.DataFrame(linhas)
    df_arestas.to_csv(caminho_saida, index=False)


def gerar_8_msts(caminho_retornos_diarios):
    dados = pd.read_csv(caminho_retornos_diarios)
    descartados = ['NTCO3.SA', 'JBSS3.SA', 'AZUL4.SA']
    dados = dados[~dados['ticker'].isin(descartados)].copy()

    col_data = 'data' if 'data' in dados.columns else 'data_reuniao'
    col_val = 'retorno' if 'retorno' in dados.columns else 'impacto_pct'

    if col_data not in dados.columns or col_val not in dados.columns:
        raise ValueError(
            f"CSV de retornos diarios precisa ter as colunas 'ticker', "
            f"'{col_data}' (data) e '{col_val}' (retorno). "
            f"Colunas encontradas: {list(dados.columns)}. "
            f"Confirme que voce esta passando o CSV de RETORNOS DIARIOS "
            f"do Davi, e nao o arestas_final.csv do Grafo 1."
        )

  
    dados['regime'] = dados[col_data].apply(atribuir_regime)
    dados = dados.dropna(subset=['regime'])

    regimes = [nome for nome, _, _ in REGIMES_SELIC if nome in dados['regime'].unique()]
    msts_por_regime = {}

    for regime in regimes:
        df_reg = dados[dados['regime'] == regime]

        matriz_dist, rotulos = calcular_distancias_mantegna(df_reg, col_data, col_val)
        G = construir_grafo_completo(matriz_dist, rotulos)
        T = prim(G)
        MST_indices = converter_para_lista_adjacencia(T, G)

        MST_rotulada = {}
        for i, vizinhos in MST_indices.items():
            MST_rotulada[rotulos[i]] = {rotulos[j]: p for j, p in vizinhos.items()}

        caminho_saida = f"mst_{regime}.csv"
        exportar_arvore(T, G, rotulos, caminho_saida)

        with open(f"resumo_mst_{regime}.txt", 'w') as arq:
            arq.write(f"Custo Total da Arvore Geradora Minima ({regime}): {round(custo_total(T, G), 4)}\n")
            arq.write(f"Periodo: {[p for n, *p in REGIMES_SELIC if n == regime][0]}\n")
            arq.write(f"Dias de pregao usados: {df_reg[col_data].nunique()}\n")

        msts_por_regime[regime] = {
            'MST': MST_rotulada,
            'rotulos': rotulos
        }

    return msts_por_regime


if __name__ == "__main__":
    gerar_8_msts('retornos_diarios_2020_2025.csv')