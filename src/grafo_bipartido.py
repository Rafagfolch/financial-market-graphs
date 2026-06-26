import math
import pandas as pd

def carregar_dados(caminho_arquivo):
    dados = pd.read_csv(caminho_arquivo)
    descartados = ['NTCO3.SA', 'JBSS3.SA', 'AZUL4.SA']
    return dados[~dados['ticker'].isin(descartados)]


def construir_grafo_bipartido(dados):
    """Equivalente a 'GrafoBip <- NovoGrafo()' + laco de AdicionarAresta
    do Algoritmo 1. Cada linha do dataset gera uma aresta evento-ativo
    com peso = Modulo(impacto)."""
    grafo = {}
    eventos = set()
    ativos = set()

    for _, linha in dados.iterrows():
        evento = linha['evento']
        ativo = linha['ativo']
        peso = linha['peso']
        impacto = linha['impacto']

        eventos.add(evento)
        ativos.add(ativo)

        if evento not in grafo:
            grafo[evento] = {}
        if ativo not in grafo:
            grafo[ativo] = {}

        grafo[evento][ativo] = {'peso': peso, 'impacto': impacto}
        grafo[ativo][evento] = {'peso': peso, 'impacto': impacto}

    return grafo, eventos, ativos


# =====================================================================
# CORRECAO - Algoritmo 1: MapearEpicentros(Dados, Limiar)
#
# ANTES: o codigo filtrava 'dados[dados['peso'] >= limiar]' e construia
# o grafo bipartido JA FILTRADO, calculando centralidade so sobre as
# arestas fortes. Isso diverge do resumo do Davi: a centralidade
# (grau ponderado / autovetor) e calculada no grafo bipartido COMPLETO
# (todo par acao-evento tem aresta); o limiar de 3% e usado SO na
# cobertura minima por conjuntos, nao na centralidade.
#
# AGORA: o grafo bipartido completo (sem filtro) e usado para
# centralidade e epicentros. O limiar so entra dentro de
# cobertura_minima(), no grafo_filtrado_por_limiar, igual ao resumo.
# =====================================================================

def mapear_epicentros(dados, limiar=None):
    """Algoritmo 1 - MapearEpicentros(Dados).

    1) Monta o GrafoBip COMPLETO (todo par acao-evento tem aresta).
    2) centralidades <- CalcularGrau(GrafoBip)
    3) epicentros <- FiltrarAcimaDaMedia(centralidades)

    O parametro 'limiar' e mantido por compatibilidade mas NAO e mais
    usado para filtrar o grafo de centralidade - segue como estava
    documentado no resumo do projeto (limiar so na cobertura).
    """
    grafo, eventos, ativos = construir_grafo_bipartido(dados)

    centralidades = calcular_grau(grafo)
    epicentros = filtrar_acima_da_media(centralidades)

    return epicentros, grafo, eventos, ativos


def calcular_grau(grafo):
    centralidades = {}
    for v in grafo:
        grau = len(grafo[v])
        centralidades[v] = grau
    return centralidades


# =====================================================================
# NOVO - Centralidade de Autovetor (power iteration / metodo das
# potencias), usando o PESO das arestas (impacto %).
#
# Conceito: a importancia de um no nao depende so de quantas conexoes
# ele tem (isso e grau), mas da importancia dos nos aos quais ele esta
# conectado, ponderada pelo peso da conexao. E uma definicao recursiva:
#   x_v = (1/lambda) * soma( peso(v,u) * x_u )  para todo vizinho u de v
#
# Resolvido iterativamente (metodo das potencias): comeca com um vetor
# uniforme, multiplica repetidamente pela matriz de adjacencia ponderada,
# e normaliza a cada passo. Converge para o autovetor principal.
#
# No nosso grafo bipartido, isso significa: um ATIVO e mais "central"
# se ele esta fortemente ligado a EVENTOS que tambem sao centrais (ex:
# reunioes que impactaram fortemente varios outros ativos importantes),
# nao so se ele tem muitas conexoes (isso e grau) ou se a soma bruta dos
# pesos dele e alta (isso seria so "grau ponderado").
# =====================================================================

def calcular_centralidade_autovetor(grafo, max_iteracoes=1000, tolerancia=1e-8):
    """Calcula centralidade de autovetor via metodo das potencias,
    usando o peso das arestas (impacto %) como peso da matriz de
    adjacencia. Retorna um dict {no: valor_normalizado}."""
    nos = list(grafo.keys())
    n = len(nos)
    if n == 0:
        return {}

    indice = {no: i for i, no in enumerate(nos)}

    # vetor inicial uniforme
    x = [1.0 / n] * n

    for _ in range(max_iteracoes):
        x_novo = [0.0] * n

        for no in nos:
            i = indice[no]
            soma = 0.0
            for vizinho, info in grafo[no].items():
                j = indice[vizinho]
                peso = info['peso']
                soma += peso * x[j]
            x_novo[i] = soma

        norma = math.sqrt(sum(v * v for v in x_novo))
        if norma == 0:
            # grafo sem nenhum peso positivo: cai para vetor uniforme
            return {no: 1.0 / n for no in nos}

        x_novo = [v / norma for v in x_novo]

        # criterio de parada: variacao entre iteracoes menor que a tolerancia
        diff = math.sqrt(sum((x_novo[i] - x[i]) ** 2 for i in range(n)))
        x = x_novo
        if diff < tolerancia:
            break

    # normaliza para o maior valor = 1.0 (mais facil de interpretar/comparar)
    maximo = max(x) if max(x) != 0 else 1.0
    return {no: x[indice[no]] / maximo for no in nos}


# --- Algoritmo 6 - Heuristica de Filtragem de Epicentros ---
def filtrar_acima_da_media(centralidades):
    if not centralidades:
        return []
    media = sum(centralidades.values()) / len(centralidades)
    epicentros = []
    for no, valor in centralidades.items():
        if valor >= media:
            epicentros.append(no)
    return epicentros


# =====================================================================
# Algoritmos EXTRAS de analise estrutural do grafo bipartido.
# Aqui SIM e onde o limiar de 3% entra (cobertura minima), conforme
# o resumo do projeto: "cobertura minima por conjuntos (greedy,
# limiar de impacto = 3%)".
# =====================================================================

def filtrar_por_limiar(dados, limiar):
    """Usado apenas para a cobertura minima, nao para centralidade."""
    return dados[dados['peso'] >= limiar].copy()


# --- (Extra) Busca de Caminho Aumentante (auxiliar) ---
def busca_aumentante(grafo, u, emparelhamento, visitados):
    for v in grafo.get(u, {}):
        if v not in visitados:
            visitados.add(v)
            if v not in emparelhamento or busca_aumentante(grafo, emparelhamento[v], emparelhamento, visitados):
                emparelhamento[v] = u
                emparelhamento[u] = v
                return True
    return False


# --- (Extra) Emparelhamento Maximo em Grafo Bipartido ---
def emparelhamento_maximo(grafo, nos_eventos):
    emparelhamento = {}
    for evento in nos_eventos:
        visitados = set()
        busca_aumentante(grafo, evento, emparelhamento, visitados)
    return emparelhamento


# --- (Extra) Cobertura Minima de Vertices (Teorema de Konig) ---
def cobertura_minima(grafo, emparelhamento, nos_eventos):
    cobertura = set()
    nao_emparelhados = nos_eventos - set(emparelhamento.keys())

    visitados_z = set(nao_emparelhados)
    fila = list(nao_emparelhados)

    while fila:
        atual = fila.pop(0)
        if atual in nos_eventos:
            for vizinho in grafo.get(atual, {}):
                if vizinho not in visitados_z and vizinho in emparelhamento and emparelhamento[vizinho] != atual:
                    visitados_z.add(vizinho)
                    fila.append(vizinho)
        else:
            vizinho = emparelhamento.get(atual)
            if vizinho is not None and vizinho not in visitados_z:
                visitados_z.add(vizinho)
                fila.append(vizinho)

    # Cobertura = Eventos nao alcancados U Ativos alcancados (Konig)
    for evento in nos_eventos:
        if evento not in visitados_z:
            cobertura.add(evento)

    for no in visitados_z:
        if no not in nos_eventos:
            cobertura.add(no)

    return cobertura


def exportar_resultados(centralidades, autovetor, epicentros, emparelhamento, cobertura, nos_eventos, caminho_saida):
    linhas = []

    for no, valor in centralidades.items():
        tipo = 'Evento' if no in nos_eventos else 'Ativo'
        linhas.append({'No': no, 'Tipo': tipo, 'Metrica': 'Centralidade_Grau', 'Valor': round(valor, 4)})

    for no, valor in autovetor.items():
        tipo = 'Evento' if no in nos_eventos else 'Ativo'
        linhas.append({'No': no, 'Tipo': tipo, 'Metrica': 'Centralidade_Autovetor', 'Valor': round(valor, 6)})

    for no in epicentros:
        tipo = 'Evento' if no in nos_eventos else 'Ativo'
        linhas.append({'No': no, 'Tipo': tipo, 'Metrica': 'Epicentro_AcimaDaMedia', 'Valor': True})

    for origem, destino in emparelhamento.items():
        if origem in nos_eventos:
            linhas.append({'No': origem, 'Tipo': 'Evento', 'Metrica': 'Emparelhamento', 'Valor': destino})

    for no in cobertura:
        tipo = 'Evento' if no in nos_eventos else 'Ativo'
        linhas.append({'No': no, 'Tipo': tipo, 'Metrica': 'Cobertura', 'Valor': 'Necessario_Monitorar'})

    df_resultados = pd.DataFrame(linhas)
    df_resultados.to_csv(caminho_saida, index=False)


def executar(usar_extras=True):
    try:
        dados = carregar_dados('arestas_final.csv')

        dados = dados.rename(columns={
            'data_reuniao': 'evento',
            'ticker': 'ativo',
            'impacto_pct': 'impacto'
        })

        dados['peso'] = dados['impacto'].abs()

    except FileNotFoundError:
        print(" Ficheiro 'arestas_final.csv' nao encontrado. A gerar dados de teste...")
        dados = pd.DataFrame({
            'evento': ['Reuniao_Normal', 'Reuniao_Crise_A', 'Reuniao_Crise_B', 'Pandemia'],
            'ativo': ['ITUB4.SA', 'PETR4.SA', 'MGLU3.SA', 'CVCB3.SA'],
            'impacto': [1.2, -0.5, -5.1, 12.8]
        })
        dados['peso'] = dados['impacto'].abs()

    limiar = 3.0

    # Algoritmo 1: MapearEpicentros(Dados) - sobre o grafo COMPLETO
    epicentros, grafo, eventos, ativos = mapear_epicentros(dados)

    if not grafo:
        print("O grafo bipartido esta vazio.")
        return

    centralidades = calcular_grau(grafo)
    autovetor = calcular_centralidade_autovetor(grafo)

    # Extras: emparelhamento maximo + cobertura minima.
    # Cobertura usa o grafo FILTRADO pelo limiar de 3%, conforme o resumo;
    # emparelhamento roda no grafo completo (nao ha mencao de limiar pra ele).
    emp = {}
    cob = set()
    if usar_extras:
        dados_filtrados = filtrar_por_limiar(dados, limiar)
        grafo_filtrado, eventos_filtrados, ativos_filtrados = construir_grafo_bipartido(dados_filtrados)

        emp = emparelhamento_maximo(grafo, eventos)
        cob = cobertura_minima(grafo_filtrado, emparelhamento_maximo(grafo_filtrado, eventos_filtrados), eventos_filtrados)

    exportar_resultados(centralidades, autovetor, epicentros, emp, cob, eventos, 'resultados_bipartido.csv')

    # GERACAO DO CSV EXTRA DAS ARESTAS DO BIPARTIDO (grafo completo)
    linhas_arestas = []
    for ev in eventos:
        for at, inf in grafo[ev].items():
            linhas_arestas.append({'evento': ev, 'ativo': at, 'peso': inf['peso'], 'impacto': inf['impacto']})
    pd.DataFrame(linhas_arestas).to_csv('bipartido_arestas.csv', index=False)

    print("Grafo bipartido processado com sucesso.")
    print(f"Epicentros (centralidade >= media, grafo completo): {len(epicentros)}")
    print(f"Centralidade de autovetor calculada para {len(autovetor)} nos.")
    if usar_extras:
        print(f"Pares no emparelhamento maximo (grafo completo): {len(emp) // 2}")
        print(f"Tamanho da cobertura minima (grafo filtrado, limiar={limiar}%): {len(cob)}")


if __name__ == "__main__":
    executar()