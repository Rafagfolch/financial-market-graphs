"""
Grafo 1 - Grafo bipartido Ações x Eventos (reuniões do COPOM)

V = ações (23 ativos)
W = eventos (reuniões do COPOM, 2020-2025)
Aresta (v, w) com peso = % de impacto no preço da ação na janela T-1 -> T+1

Este script:
1. Constrói o grafo bipartido a partir do CSV de arestas
2. Calcula medidas de centralidade adaptadas ao caso (grafo ponderado e completo)
3. Exporta um resumo para uso no relatório
"""

import pandas as pd
import networkx as nx

# =========================================================
# 1. Carregar dados e construir o grafo bipartido
# =========================================================
df = pd.read_csv("arestas_final.csv")

G = nx.Graph()

# Nós do tipo "ação" (bipartite=0) e do tipo "evento" (bipartite=1)
acoes = df['ticker'].unique().tolist()
eventos = df['data_reuniao'].unique().tolist()

G.add_nodes_from(acoes, bipartite=0, tipo='acao')
G.add_nodes_from(eventos, bipartite=1, tipo='evento')

# Arestas com peso = impacto percentual (guardamos o valor absoluto como peso
# "de intensidade", mas guardamos também o sinal original como atributo,
# já que para centralidade/cobertura/emparelhamento normalmente interessa
# a MAGNITUDE do impacto, não a direção)
for _, row in df.iterrows():
    G.add_edge(
        row['ticker'],
        row['data_reuniao'],
        peso=abs(row['impacto_pct']),       # magnitude (usada nos algoritmos)
        impacto_pct=row['impacto_pct'],     # valor original com sinal
        direcao_selic=row['direcao'],
    )

print(f"Grafo bipartido construído:")
print(f"  Nós (ações): {len(acoes)}")
print(f"  Nós (eventos): {len(eventos)}")
print(f"  Arestas: {G.number_of_edges()}")
print(f"  É bipartido? {nx.is_bipartite(G)}")

# =========================================================
# 2. Centralidade de grau ponderada (degree centrality ponderado)
#    Para cada ação: soma das magnitudes de impacto em todos os eventos
#    -> quanto maior, mais "sensível à Selic" essa ação é, no agregado
# =========================================================
centralidade_grau_ponderada = {}
for no in G.nodes():
    soma_pesos = sum(dados['peso'] for _, _, dados in G.edges(no, data=True))
    centralidade_grau_ponderada[no] = soma_pesos

# Separar ranking de ações (mais sensíveis à Selic) e eventos (mais impactantes)
ranking_acoes = sorted(
    [(n, v) for n, v in centralidade_grau_ponderada.items() if n in acoes],
    key=lambda x: x[1], reverse=True
)
ranking_eventos = sorted(
    [(n, v) for n, v in centralidade_grau_ponderada.items() if n in eventos],
    key=lambda x: x[1], reverse=True
)

print("\nTop 5 ações mais sensíveis à Selic (soma de |impacto| em todas reuniões):")
for ticker, valor in ranking_acoes[:5]:
    print(f"  {ticker}: {valor:.2f}")

print("\nTop 5 reuniões do COPOM com maior impacto agregado no mercado:")
for data, valor in ranking_eventos[:5]:
    print(f"  {data}: {valor:.2f}")

# =========================================================
# 3. Centralidade de autovetor (eigenvector centrality)
#    Em grafo bipartido ponderado, identifica ações/eventos que são
#    centrais não só pela soma bruta, mas pela conexão com OUTROS nós
#    que também são centrais (efeito de propagação)
# =========================================================
try:
    centralidade_autovetor = nx.eigenvector_centrality(G, weight='peso', max_iter=1000)
    ranking_autovetor_acoes = sorted(
        [(n, v) for n, v in centralidade_autovetor.items() if n in acoes],
        key=lambda x: x[1], reverse=True
    )
    print("\nTop 5 ações por centralidade de autovetor:")
    for ticker, valor in ranking_autovetor_acoes[:5]:
        print(f"  {ticker}: {valor:.4f}")
except nx.PowerIterationFailedConvergence:
    print("\n[aviso] Eigenvector centrality não convergiu - considerar normalizar pesos.")

# =========================================================
# 4. Exporta resumo para uso no relatório / próximas etapas
# =========================================================
resumo = pd.DataFrame(ranking_acoes, columns=['ticker', 'centralidade_grau_ponderada'])
resumo.to_csv("centralidade_acoes.csv", index=False)

resumo_eventos = pd.DataFrame(ranking_eventos, columns=['data_reuniao', 'centralidade_grau_ponderada'])
resumo_eventos.to_csv("centralidade_eventos.csv", index=False)

print("\nArquivos salvos: centralidade_acoes.csv, centralidade_eventos.csv")
