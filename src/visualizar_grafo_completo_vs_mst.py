"""
Este script gera 8 figuras DIDATICAS, uma para cada regime de Selic,
mostrando de onde cada MST foi escolhida.

Diferente das 8 figuras principais (que mostram so a MST, ja
"pronta"), estas figuras mostram o GRAFO COMPLETO de correlacao entre
as acoes de cada regime (todas as conexoes possiveis, desenhadas em
cinza claro e fino), com as arestas que o algoritmo de Prim escolheu
para a MST destacadas por cima, nas mesmas cores e estilo das outras
figuras - incluindo a mesma legenda de cores (mapa de calor) usada la.
"""

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import FancyBboxPatch
from networkx.algorithms.community import louvain_communities

plt.rcParams['font.family'] = 'DejaVu Sans'

COR_FUNDO = '#F7F5F0'

# Nome e periodo de cada um dos 8 regimes de Selic
INFO_REGIMES = {
    1: ("Corte (pandemia)", "2020-02-05", "2020-08-05"),
    2: ("Manutenção (baixa)", "2020-09-16", "2021-01-20"),
    3: ("Alta", "2021-03-17", "2022-08-03"),
    4: ("Manutenção (alta)", "2022-09-21", "2023-06-21"),
    5: ("Corte", "2023-08-02", "2024-05-08"),
    6: ("Manutenção", "2024-06-19", "2024-07-31"),
    7: ("Alta", "2024-09-18", "2025-06-18"),
    8: ("Manutenção (alta)", "2025-07-30", "2025-12-10"),
}

# Mesmas cores de comunidade usadas nas outras 8 figuras da MST
CORES_COMUNIDADES = [
    ('#7FA98C', '#3E6B4D'),  # verde
    ('#A893C2', '#5F4480'),  # lilás
    ('#9B9B93', '#5C5C54'),  # cinza
    ('#8C7A6B', '#4F4137'),  # marrom
    ('#6FA39A', '#2F5C54'),  # verde petróleo
    ('#B295A8', '#6B4A5C'),  # malva
    ('#7D8B6E', '#42502F'),  # verde oliva
]

MAPA_DE_CALOR = mcolors.LinearSegmentedColormap.from_list(
    'calor', ['#3D6FA8', '#7FA8C8', '#D4B85A', '#D07949', '#B23A2E']
)

# Cor das arestas que nao entraram na MST:
COR_ARESTA_DESCARTADA = '#C9C5BC'


def montar_grafo_completo_do_regime(numero_regime, data_inicio, data_fim):
    """Le os retornos diarios, filtra pelo periodo do regime, e calcula
    a correlacao entre todas as acoes (grafo completo, nao so a MST).

    Mesma logica usada no arvoreGerado.py: remove colunas sem nenhum
    dado no periodo, e nunca usa fillna(0) (isso distorceria a
    correlacao)."""
    retornos = pd.read_csv('retornos_diarios_2020_2025.csv')
    descartados = ['NTCO3.SA', 'JBSS3.SA', 'AZUL4.SA']
    retornos = retornos[~retornos['ticker'].isin(descartados)]

    retornos_do_regime = retornos[(retornos['data'] >= data_inicio) &
                                   (retornos['data'] <= data_fim)]
    tabela = retornos_do_regime.pivot_table(index='data', columns='ticker', values='retorno')
    tabela = tabela.dropna(axis=1, how='all')

    matriz_correlacao = tabela.corr(method='pearson')
    acoes = list(matriz_correlacao.columns)

    grafo_completo = nx.Graph()
    for i, acao1 in enumerate(acoes):
        for acao2 in acoes[i + 1:]:
            correlacao = matriz_correlacao.loc[acao1, acao2]
            if pd.notna(correlacao):
                grafo_completo.add_edge(acao1, acao2, correlacao=correlacao)

    return grafo_completo


def ler_arestas_da_mst(numero_regime):
    """Le o CSV da MST ja calculada, e devolve o conjunto de pares de
    acoes que fazem parte dela (para sabermos quais arestas destacar)."""
    tabela = pd.read_csv(f"mst_Regime_{numero_regime}.csv")
    arestas_da_mst = set()
    for _, linha in tabela.iterrows():
        par = tuple(sorted([linha['Origem'], linha['Destino']]))
        arestas_da_mst.add(par)
    return arestas_da_mst


def desenhar_legenda_de_cores(figura, valor_minimo, valor_maximo):
    """Desenha a legenda embaixo da figura,
    explicando o que cada cor de linha significa - mesma legenda
    usada nas outras 8 figuras da MST."""
    mapa_escalar = plt.cm.ScalarMappable(
        cmap=MAPA_DE_CALOR,
        norm=plt.Normalize(vmin=valor_minimo, vmax=valor_maximo)
    )
    eixo_legenda = figura.add_axes([0.30, 0.04, 0.40, 0.018])
    barra_cores = figura.colorbar(mapa_escalar, cax=eixo_legenda, orientation='horizontal')
    barra_cores.set_label('Correlação entre retornos diários (mais fraca → mais forte)',
                           fontsize=9.5, color='#5C5C54')
    barra_cores.ax.tick_params(labelsize=8.5, colors='#5C5C54')
    barra_cores.outline.set_edgecolor('#A8A29A')


def desenhar_caixinha(eixo, x, y, texto, cor_de_dentro, cor_da_borda):
    """Desenha uma caixinha retangular com o nome da acao dentro.

    A largura da caixinha muda de acordo com o tamanho do texto, para
    o nome nunca ficar cortado."""
    largura = 0.85 + len(texto) * 0.165
    altura = 0.50

    caixinha = FancyBboxPatch(
        (x - largura / 2, y - altura / 2), largura, altura,
        boxstyle="round,pad=0,rounding_size=0.09",
        linewidth=1.5,
        edgecolor=cor_da_borda,
        facecolor=cor_de_dentro,
        zorder=3,
    )
    eixo.add_patch(caixinha)

    eixo.text(
        x, y, texto,
        ha='center', va='center',
        fontsize=11.5, fontweight='bold',
        color=cor_da_borda,
        zorder=4,
    )


def calcular_posicoes(grafo_completo, numero_regime):
    """Calcula a posicao de cada acao no desenho, usando Kamada-Kawai
    so sobre as arestas da MST (as arestas extras, em cinza, sao
    desenhadas depois nas mesmas posicoes).

    Usa a distancia ja salva no CSV da MST, e nao a distancia
    recalculada a partir da matriz de correlacao completa - assim a
    posicao de cada acao fica igual a da figura simples (mst_simples.py)."""
    tabela_mst = pd.read_csv(f"mst_Regime_{numero_regime}.csv")
    grafo_so_da_mst = nx.Graph()
    for _, linha in tabela_mst.iterrows():
        acao1, acao2 = linha['Origem'], linha['Destino']
        distancia = linha['Distancia_Mantegna']
        grafo_so_da_mst.add_edge(acao1, acao2, distancia=distancia)

    posicoes = nx.kamada_kawai_layout(grafo_so_da_mst, weight='distancia')

    xs = [p[0] for p in posicoes.values()]
    ys = [p[1] for p in posicoes.values()]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    largura_x = (x_max - x_min) or 1
    largura_y = (y_max - y_min) or 1

    posicoes_ajustadas = {}
    for no, (x, y) in posicoes.items():
        novo_x = (x - x_min) / largura_x * 19 + 2.5
        novo_y = (y - y_min) / largura_y * 14 + 2.5
        posicoes_ajustadas[no] = (novo_x, novo_y)

    return posicoes_ajustadas


def gerar_figura_didatica(numero_regime, nome_do_regime, data_inicio, data_fim):
    """Funcao principal: monta a figura completa (grafo cinza + MST
    destacada) e salva como PNG."""

    grafo_completo = montar_grafo_completo_do_regime(numero_regime, data_inicio, data_fim)
    arestas_da_mst = ler_arestas_da_mst(numero_regime)

    # Descobre os grupos/comunidades, olhando so para a MST - igual
    # as outras 8 figuras fazem. O grafo precisa ser montado na mesma
    # ordem das linhas do CSV (e nao a partir do set de arestas), para
    # o Louvain numerar as comunidades igual ao mst_simples.py.
    tabela_mst = pd.read_csv(f"mst_Regime_{numero_regime}.csv")
    grafo_so_da_mst = nx.Graph()
    for _, linha in tabela_mst.iterrows():
        acao1, acao2 = linha['Origem'], linha['Destino']
        correlacao = grafo_completo[acao1][acao2]['correlacao']
        grafo_so_da_mst.add_edge(acao1, acao2, correlacao=correlacao)

    comunidades = louvain_communities(grafo_so_da_mst, weight='correlacao', seed=42)
    cor_de_cada_acao = {}
    for indice, comunidade in enumerate(comunidades):
        cor_dentro, cor_borda = CORES_COMUNIDADES[indice % len(CORES_COMUNIDADES)]
        for acao in comunidade:
            cor_de_cada_acao[acao] = (cor_dentro, cor_borda)

    posicoes = calcular_posicoes(grafo_completo, numero_regime)

    figura, eixo = plt.subplots(figsize=(13, 10))
    figura.patch.set_facecolor(COR_FUNDO)
    eixo.set_facecolor(COR_FUNDO)

    # Primeiro: desenha todas as arestas do grafo completo, em cinza
    # claro e fino - estas sao as conexoes que o algoritmo de Prim
    # nao escolheu para a MST
    for acao1, acao2, dados in grafo_completo.edges(data=True):
        par = tuple(sorted([acao1, acao2]))
        if par in arestas_da_mst:
            continue  # essa aresta sera desenhada depois, destacada

        if acao1 not in posicoes or acao2 not in posicoes:
            continue
        x1, y1 = posicoes[acao1]
        x2, y2 = posicoes[acao2]
        eixo.plot([x1, x2], [y1, y2], color=COR_ARESTA_DESCARTADA,
                  linewidth=0.5, alpha=0.5, zorder=0, solid_capstyle='round')

    # Depois: desenha so as arestas da MST, destacadas com o mesmo
    # mapa de calor usado nas outras 8 figuras
    todas_correlacoes_da_mst = [grafo_completo[a1][a2]['correlacao'] for a1, a2 in arestas_da_mst]
    correlacao_minima = min(todas_correlacoes_da_mst)
    correlacao_maxima = max(todas_correlacoes_da_mst)
    intervalo = (correlacao_maxima - correlacao_minima) or 1

    for _, linha in tabela_mst.iterrows():
        acao1, acao2 = linha['Origem'], linha['Destino']
        x1, y1 = posicoes[acao1]
        x2, y2 = posicoes[acao2]
        correlacao = grafo_completo[acao1][acao2]['correlacao']
        posicao_na_escala = (correlacao - correlacao_minima) / intervalo
        cor_da_linha = MAPA_DE_CALOR(posicao_na_escala)
        grossura_da_linha = 1.2 + posicao_na_escala * 4.5
        eixo.plot([x1, x2], [y1, y2], color=cor_da_linha, linewidth=grossura_da_linha,
                  alpha=0.9, zorder=1, solid_capstyle='round')

    # Desenha as caixinhas por cima de tudo
    for acao, (x, y) in posicoes.items():
        cor_dentro, cor_borda = cor_de_cada_acao[acao]
        nome_curto = acao.replace('.SA', '')
        desenhar_caixinha(eixo, x, y, nome_curto, cor_dentro, cor_borda)

    eixo.set_xlim(0, 22.5)
    eixo.set_ylim(0, 17.5)
    eixo.axis('off')

    n_total_arestas = grafo_completo.number_of_edges()
    n_arestas_mst = len(arestas_da_mst)
    data_inicio_fmt = pd.to_datetime(data_inicio).strftime('%d/%m/%Y')
    data_fim_fmt = pd.to_datetime(data_fim).strftime('%d/%m/%Y')

    eixo.set_title(
        f"Como a MST é escolhida: grafo completo × árvore final\n"
        f"Regime {numero_regime} ({nome_do_regime}, {data_inicio_fmt} a {data_fim_fmt})",
        fontsize=15, fontweight='bold', color='#2C2C2A', pad=14,
    )
    eixo.text(
        11.25, 17,
        f"Cinza: {n_total_arestas - n_arestas_mst} conexões possíveis não escolhidas   |   "
        f"Colorido: {n_arestas_mst} arestas da MST (Prim)",
        ha='center', fontsize=11, color='#5C5C54', style='italic',
    )

    desenhar_legenda_de_cores(figura, correlacao_minima, correlacao_maxima)

    plt.subplots_adjust(bottom=0.12)
    nome_arquivo = f"figura_didatica_mst_regime{numero_regime}.png"
    plt.savefig(nome_arquivo, dpi=160, bbox_inches='tight', facecolor=COR_FUNDO)
    plt.close()

    print(f"Figura didática salva: {nome_arquivo}")
    print(f"  Grafo completo: {n_total_arestas} conexões possíveis")
    print(f"  MST: {n_arestas_mst} arestas escolhidas")


if __name__ == "__main__":
    for numero_regime, (nome_do_regime, data_inicio, data_fim) in INFO_REGIMES.items():
        gerar_figura_didatica(numero_regime, nome_do_regime, data_inicio, data_fim)

    print("\nTodas as 8 figuras didáticas foram geradas com sucesso!")