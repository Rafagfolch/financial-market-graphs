"""
Este script desenha as 8 MSTs (Arvores Geradoras Minimas) do Grafo 2,
uma para cada regime de Selic.

Para cada regime:
1. Le o arquivo CSV com as arestas da MST (gerado pelo arvoreGerado.py)
2. Detecta as comunidades de acoes mais parecidas entre si (Louvain)
3. Calcula a posicao de cada acao no desenho (Kamada-Kawai)
4. Desenha tudo: caixinhas para as acoes, linhas coloridas para as
   conexoes, e uma legenda explicando as cores
"""

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import FancyBboxPatch
from networkx.algorithms.community import louvain_communities

plt.rcParams['font.family'] = 'DejaVu Sans'

# Nome e periodo de cada um dos 8 regimes de Selic, so para escrever
# no titulo de cada figura
INFO_REGIMES = {
    1: "Corte (pandemia) - 05/02/2020 a 05/08/2020",
    2: "Manutenção (baixa) - 16/09/2020 a 20/01/2021",
    3: "Alta - 17/03/2021 a 03/08/2022",
    4: "Manutenção (alta) - 21/09/2022 a 21/06/2023",
    5: "Corte - 02/08/2023 a 08/05/2024",
    6: "Manutenção - 19/06/2024 a 31/07/2024",
    7: "Alta - 18/09/2024 a 18/06/2025",
    8: "Manutenção (alta) - 30/07/2025 a 10/12/2025",
}

# Cor de fundo da figura
COR_FUNDO = '#F7F5F0'

# Cores usadas para colorir cada comunidade detectada. Cada item da
# lista tem 2 cores: a cor de dentro da caixinha e a cor da borda/texto.
# Escolhemos cores que nao sao azul nem vermelho, porque essas duas
# cores ja sao usadas nas linhas (ver MAPA_DE_CALOR abaixo) - assim
# as cores das caixinhas nunca se confundem com as cores das linhas.
CORES_COMUNIDADES = [
    ('#7FA98C', '#3E6B4D'),  # verde
    ('#A893C2', '#5F4480'),  # lilás
    ('#9B9B93', '#5C5C54'),  # cinza
    ('#8C7A6B', '#4F4137'),  # marrom
    ('#6FA39A', '#2F5C54'),  # verde petróleo
    ('#B295A8', '#6B4A5C'),  # malva
    ('#7D8B6E', '#42502F'),  # verde oliva
]

# Mapa de cores tipo "termometro": azul = correlacao fraca,
# vermelho = correlacao forte. Usamos isso para colorir as linhas.
MAPA_DE_CALOR = mcolors.LinearSegmentedColormap.from_list(
    'calor', ['#3D6FA8', '#7FA8C8', '#D4B85A', '#D07949', '#B23A2E']
)


def ler_mst_do_regime(numero_regime):
    """Le o arquivo CSV de um regime e monta um grafo do networkx.

    O CSV tem a distancia de Mantegna entre cada par de acoes. Como a
    correlacao e mais facil de entender (quanto mais perto de 1, mais
    parecidas as acoes sao), calculamos ela de volta a partir da
    distancia, usando a formula inversa de Mantegna."""
    tabela = pd.read_csv(f"mst_Regime_{numero_regime}.csv")
    grafo = nx.Graph()

    for _, linha in tabela.iterrows():
        distancia = linha['Distancia_Mantegna']
        correlacao = 1 - (distancia ** 2) / 2  # formula inversa de Mantegna
        grafo.add_edge(linha['Origem'], linha['Destino'],
                        distancia=distancia, correlacao=correlacao)

    return grafo


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


def calcular_posicoes(grafo):
    """Calcula em que posicao (x, y) cada acao vai ficar no desenho.

    Usamos o algoritmo Kamada-Kawai, que tenta deixar acoes muito
    correlacionadas mais proximas entre si no desenho. Depois disso,
    so reescalamos as posicoes para caberem bem na figura."""
    posicoes = nx.kamada_kawai_layout(grafo, weight='distancia')

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


def desenhar_legenda_de_cores(figura, valor_minimo, valor_maximo):
    """Desenha a legenda embaixo da figura,
    explicando o que cada cor de linha significa."""
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


def gerar_figura(numero_regime):
    """Funcao principal: monta a figura completa de um regime e salva
    como arquivo PNG."""

    grafo = ler_mst_do_regime(numero_regime)

    # Descobre os grupos (comunidades) de acoes mais parecidas entre si
    comunidades = louvain_communities(grafo, weight='correlacao', seed=42)

    # Decide a cor de cada acao, de acordo com a comunidade dela
    cor_de_cada_acao = {}
    for indice, comunidade in enumerate(comunidades):
        cor_dentro, cor_borda = CORES_COMUNIDADES[indice % len(CORES_COMUNIDADES)]
        for acao in comunidade:
            cor_de_cada_acao[acao] = (cor_dentro, cor_borda)

    posicoes = calcular_posicoes(grafo)

    figura, eixo = plt.subplots(figsize=(12, 9))
    figura.patch.set_facecolor(COR_FUNDO)
    eixo.set_facecolor(COR_FUNDO)

    # Para colorir as linhas como um "termometro", precisamos saber
    # qual e a menor e a maior correlacao deste regime
    todas_correlacoes = [dados['correlacao'] for _, _, dados in grafo.edges(data=True)]
    correlacao_minima = min(todas_correlacoes)
    correlacao_maxima = max(todas_correlacoes)
    intervalo = (correlacao_maxima - correlacao_minima) or 1

    # Desenha cada linha (aresta) do grafo, ligando duas acoes
    for acao1, acao2, dados in grafo.edges(data=True):
        x1, y1 = posicoes[acao1]
        x2, y2 = posicoes[acao2]

        correlacao = dados['correlacao']
        posicao_na_escala = (correlacao - correlacao_minima) / intervalo
        cor_da_linha = MAPA_DE_CALOR(posicao_na_escala)
        grossura_da_linha = 1.2 + posicao_na_escala * 4.5

        eixo.plot([x1, x2], [y1, y2], color=cor_da_linha, linewidth=grossura_da_linha,
                  alpha=0.85, zorder=1, solid_capstyle='round')

    # Desenha cada caixinha (no) por cima das linhas
    for acao, (x, y) in posicoes.items():
        cor_dentro, cor_borda = cor_de_cada_acao[acao]
        nome_curto = acao.replace('.SA', '')
        desenhar_caixinha(eixo, x, y, nome_curto, cor_dentro, cor_borda)

    eixo.set_xlim(0, 22.5)
    eixo.set_ylim(0, 17.5)
    eixo.axis('off')  # esconde os eixos x e y, que nao fazem sentido aqui

    eixo.set_title(
        f"Grafo 2 — MST de correlação entre ações\n"
        f"Regime {numero_regime}: {INFO_REGIMES[numero_regime]}",
        fontsize=15, fontweight='bold', color='#2C2C2A', pad=14,
    )
    eixo.text(
        11.25, 17, f"{len(comunidades)} comunidades detectadas (Louvain)",
        ha='center', fontsize=11.5, color='#5C5C54', style='italic',
    )

    desenhar_legenda_de_cores(figura, correlacao_minima, correlacao_maxima)

    plt.subplots_adjust(bottom=0.12)
    nome_do_arquivo = f"figura_mst_regime{numero_regime}.png"
    plt.savefig(nome_do_arquivo, dpi=160, bbox_inches='tight', facecolor=COR_FUNDO)
    plt.close()

    print(f"Regime {numero_regime}: {len(grafo.nodes())} acoes, "
          f"{len(grafo.edges())} conexoes, {len(comunidades)} comunidades "
          f"-> salvo em {nome_do_arquivo}")


# Roda a geracao das 8 figuras, uma para cada regime de Selic
if __name__ == "__main__":
    for numero_regime in range(1, 9):
        gerar_figura(numero_regime)

    print("\nTodas as 8 figuras foram geradas com sucesso!")