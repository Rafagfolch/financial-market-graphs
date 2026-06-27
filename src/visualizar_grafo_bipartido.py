"""
Este script desenha o Grafo 1 (bipartido entre Acoes e Reunioes do
COPOM).

Como o grafo real tem 23 acoes e 48 reunioes (muitas conexoes para
caber numa figura legivel), desenhamos so uma amostra: as 8 acoes
mais importantes (maior centralidade de autovetor) ligadas as 6
reunioes que mais impactaram o mercado.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import FancyBboxPatch

plt.rcParams['font.family'] = 'DejaVu Sans'


# Cor de fundo da figura
COR_FUNDO = '#F7F5F0'

# Cores das caixinhas. Escolhemos cores que nao sao azul nem vermelho,
# porque essas duas cores ja sao usadas nas linhas (ver MAPA_DE_CALOR
# abaixo) - assim nunca ha confusao entre a cor da caixinha e a cor
# da linha.
COR_CAIXINHA_ACAO = ('#7FA98C', '#3E6B4D')      # verde
COR_CAIXINHA_EVENTO = ('#A893C2', '#5F4480')    # lilás

# Mapa de cores tipo "termometro": azul = impacto fraco,
# vermelho = impacto forte. Usamos isso para colorir as linhas.
MAPA_DE_CALOR = mcolors.LinearSegmentedColormap.from_list(
    'calor', ['#3D6FA8', '#7FA8C8', '#D4B85A', '#D07949', '#B23A2E']
)


def desenhar_caixinha(eixo, x, y, texto, cor_de_dentro, cor_da_borda, tamanho_da_fonte=10.5):
    """Desenha uma caixinha retangular com um texto dentro (nome da
    acao ou data da reuniao).

    A largura da caixinha muda de acordo com o tamanho do texto, para
    o texto nunca ficar cortado."""
    largura = 0.5 + len(texto) * 0.105
    altura = 0.42

    caixinha = FancyBboxPatch(
        (x - largura / 2, y - altura / 2), largura, altura,
        boxstyle="round,pad=0,rounding_size=0.08",
        linewidth=1.4,
        edgecolor=cor_da_borda,
        facecolor=cor_de_dentro,
        zorder=3,
    )
    eixo.add_patch(caixinha)

    eixo.text(
        x, y, texto,
        ha='center', va='center',
        fontsize=tamanho_da_fonte, fontweight='bold',
        color=cor_da_borda,
        zorder=4,
    )


def calcular_posicoes_em_coluna(lista_de_nomes, x_da_coluna, y_topo, y_base):
    """Calcula a posicao (x, y) de cada item de uma lista, distribuindo
    todos eles em uma unica coluna vertical, do topo para a base."""
    posicoes = {}
    quantidade = len(lista_de_nomes)
    espaco_entre_itens = (y_topo - y_base) / (quantidade - 1) if quantidade > 1 else 0

    for indice, nome in enumerate(lista_de_nomes):
        posicoes[nome] = (x_da_coluna, y_topo - indice * espaco_entre_itens)

    return posicoes


def desenhar_legenda_de_cores(figura, valor_minimo, valor_maximo):
    """Desenha a legenda embaixo da figura,
    explicando o que cada cor de linha significa."""
    mapa_escalar = plt.cm.ScalarMappable(
        cmap=MAPA_DE_CALOR,
        norm=plt.Normalize(vmin=valor_minimo, vmax=valor_maximo)
    )
    eixo_legenda = figura.add_axes([0.32, 0.045, 0.38, 0.018])
    barra_cores = figura.colorbar(mapa_escalar, cax=eixo_legenda, orientation='horizontal')
    barra_cores.set_label('Impacto percentual no preço (mais fraco → mais forte)',
                           fontsize=9.5, color='#5C5C54')
    barra_cores.ax.tick_params(labelsize=8.5, colors='#5C5C54')
    barra_cores.outline.set_edgecolor('#A8A29A')


def gerar_figura_bipartido():
    """Funcao principal: monta a figura completa e salva como PNG."""

    amostra = pd.read_csv('amostra_bipartido.csv')

    # Ordena as acoes e os eventos do maior impacto total para o menor,
    # so para a figura ficar mais organizada de cima para baixo
    acoes = sorted(
        amostra['ativo'].unique(),
        key=lambda acao: -amostra[amostra['ativo'] == acao]['peso'].sum()
    )
    eventos = sorted(
        amostra['evento'].unique(),
        key=lambda evento: -amostra[amostra['evento'] == evento]['peso'].sum()
    )

    figura, eixo = plt.subplots(figsize=(12, 9.5))
    figura.patch.set_facecolor(COR_FUNDO)
    eixo.set_facecolor(COR_FUNDO)

    # Acoes ficam numa coluna a esquerda, eventos numa coluna a direita
    x_coluna_acoes, x_coluna_eventos = 3.0, 11.0
    y_topo, y_base = 12.5, 1.5

    posicoes_acoes = calcular_posicoes_em_coluna(acoes, x_coluna_acoes, y_topo, y_base)
    posicoes_eventos = calcular_posicoes_em_coluna(eventos, x_coluna_eventos, y_topo, y_base)

    # Para colorir as linhas como um "termometro", precisamos saber
    # qual e o menor e o maior peso (impacto) desta amostra
    peso_minimo = amostra['peso'].min()
    peso_maximo = amostra['peso'].max()
    intervalo = (peso_maximo - peso_minimo) or 1

    # Desenha cada linha (aresta) ligando uma acao a um evento
    for _, linha in amostra.iterrows():
        x1, y1 = posicoes_acoes[linha['ativo']]
        x2, y2 = posicoes_eventos[linha['evento']]

        peso = linha['peso']
        posicao_na_escala = (peso - peso_minimo) / intervalo
        cor_da_linha = MAPA_DE_CALOR(posicao_na_escala)
        grossura_da_linha = 0.5 + posicao_na_escala * 4.0

        eixo.plot([x1, x2], [y1, y2], color=cor_da_linha, linewidth=grossura_da_linha,
                  alpha=0.85, zorder=1, solid_capstyle='round')

    # Desenha as caixinhas das acoes (coluna esquerda)
    for acao, (x, y) in posicoes_acoes.items():
        nome_curto = acao.replace('.SA', '')
        desenhar_caixinha(eixo, x, y, nome_curto, *COR_CAIXINHA_ACAO)

    # Desenha as caixinhas dos eventos (coluna direita), com a data
    # formatada em dd/mm/aaaa
    for evento, (x, y) in posicoes_eventos.items():
        data_formatada = pd.to_datetime(evento).strftime('%d/%m/%Y')
        desenhar_caixinha(eixo, x, y, data_formatada, *COR_CAIXINHA_EVENTO, tamanho_da_fonte=10)

    # Escreve o titulo de cada coluna, no topo da figura
    eixo.text(x_coluna_acoes, y_topo + 0.8, "Ações", ha='center', fontsize=13,
              fontweight='bold', color='#2C2C2A')
    eixo.text(x_coluna_eventos, y_topo + 0.8, "Reuniões do COPOM", ha='center', fontsize=13,
              fontweight='bold', color='#2C2C2A')

    eixo.set_xlim(0, 14)
    eixo.set_ylim(0, 14.5)
    eixo.axis('off')  # esconde os eixos x e y, que nao fazem sentido aqui

    eixo.set_title(
        "Grafo 1 — Rede bipartida ações × eventos do COPOM\n"
        "Amostra: 8 ações de maior centralidade de autovetor × 6 reuniões de maior impacto agregado",
        fontsize=14.5, fontweight='bold', color='#2C2C2A', pad=18,
    )
    eixo.text(
        7, 13.85,
        "Espessura e cor da linha = magnitude do impacto percentual (T−1 → T+1)",
        ha='center', fontsize=11, color='#5C5C54', style='italic',
    )

    # Nota explicando que essa figura e so uma amostra do grafo real
    eixo.text(
        0.3, 0.85,
        "Grafo real: 23 ações × 48 reuniões, 1077 arestas — amostra ilustrativa para legibilidade.",
        ha='left', fontsize=9.5, color='#8B8880', style='italic',
    )

    desenhar_legenda_de_cores(figura, peso_minimo, peso_maximo)

    plt.subplots_adjust(bottom=0.13)
    plt.savefig('figura_bipartido_amostra.png', dpi=160, bbox_inches='tight',
                facecolor=COR_FUNDO)
    plt.close()
    print("Figura salva: figura_bipartido_amostra.png")


if __name__ == "__main__":
    gerar_figura_bipartido()