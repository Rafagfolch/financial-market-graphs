import pandas as pd

def carregar_dados(caminho_arquivo):
    return pd.read_csv(caminho_arquivo)

def construir_grafo_bipartido_manual(dados):
    grafo = {}
    eventos = set()
    ativos = set()

    for item, linha in dados.iterrows():
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

def calcular_centralidade(grafo, nos_eventos):
    centralidade = {}
    total_ativos = len([no for no in grafo if no not in nos_eventos])

    for evento in nos_eventos:
        if evento in grafo and total_ativos > 0:
            centralidade[evento] = len(grafo[evento]) / total_ativos
        else:
            centralidade[evento] = 0.0

    return centralidade

def emparelhamento_maximo(grafo, nos_eventos):
    emparelhamento = {}
    visitados = set()

    def busca_aumentante(u):
        for v in grafo.get(u, {}):
            if v not in visitados:
                visitados.add(v)
                if v not in emparelhamento or busca_aumentante(emparelhamento[v]):
                    emparelhamento[v] = u
                    emparelhamento[u] = v
                    return True
        return False

    for evento in nos_eventos:
        visitados.clear()
        busca_aumentante(evento)

    return emparelhamento

def cobertura_minima(grafo, emparelhamento, nos_eventos):
    cobertura = set()
    nao_emparelhados = nos_eventos - set(emparelhamento.keys())
    
    visitados_z = set()
    fila = list(nao_emparelhados)
    
    for no in fila:
        visitados_z.add(no)
        
    while fila:
        atual = fila.pop(0)
        if atual in nos_eventos:
            for vizinho in grafo.get(atual, {}):
                if vizinho not in visitados_z and vizinho in emparelhamento and emparelhamento[vizinho] != atual:
                    visitados_z.add(vizinho)
                    fila.append(vizinho)
        else:
            vizinho = emparelhamento.get(atual)
            if vizinho and vizinho not in visitados_z:
                visitados_z.add(vizinho)
                fila.append(vizinho)
                
    for evento in nos_eventos:
        if evento not in visitados_z:
            cobertura.add(evento)
            
    for no in visitados_z:
        if no not in nos_eventos:
            cobertura.add(no)
            
    return cobertura

def exportar_resultados(centralidade, emparelhamento, cobertura, nos_eventos, caminho_saida):
    linhas = []

    for no, valor in centralidade.items():
        tipo = 'Evento' if no in nos_eventos else 'Ativo'
        linhas.append({'No': no, 'Tipo': tipo, 'Metrica': 'Centralidade', 'Valor': round(valor, 4)})

    for origem, destino in emparelhamento.items():
        if origem in nos_eventos:
            linhas.append({'No': origem, 'Tipo': 'Evento', 'Metrica': 'Emparelhamento', 'Valor': destino})

    for no in cobertura:
        tipo = 'Evento' if no in nos_eventos else 'Ativo'
        linhas.append({'No': no, 'Tipo': tipo, 'Metrica': 'Cobertura', 'Valor': 'Necessario_Monitorar'})

    df_resultados = pd.DataFrame(linhas)
    df_resultados.to_csv(caminho_saida, index=False)

def executar():
    try:
        dados = carregar_dados('arestas_final.csv')
        
        dados = dados.rename(columns={
            'data_reuniao': 'evento',
            'ticker': 'ativo',
            'impacto_pct': 'impacto'
        })
        
        dados['peso'] = dados['impacto'].abs()
        dados = dados[dados['peso'] > 3.0]
        
    except FileNotFoundError:
        print(" Ficheiro 'arestas_final.csv' não encontrado. A gerar dados de teste...")
        dados = pd.DataFrame({
            'evento': ['Reuniao_Normal', 'Reuniao_Crise_A', 'Reuniao_Crise_B', 'Pandemia'],
            'ativo': ['ITUB4.SA', 'PETR4.SA', 'MGLU3.SA', 'CVCB3.SA'],
            'impacto': [1.2, -0.5, -5.1, 12.8]
        })
        dados['peso'] = dados['impacto'].abs()
        dados = dados[dados['peso'] > 3.0]

    if dados.empty:
        print("O grafo está vazio. Nenhum ativo teve um impacto superior a 3%.")
        return

    grafo, eventos, ativos = construir_grafo_bipartido_manual(dados)
    
    cent = calcular_centralidade(grafo, eventos)
    emp = emparelhamento_maximo(grafo, eventos)
    cob = cobertura_minima(grafo, emp, eventos)
    
    exportar_resultados(cent, emp, cob, eventos, 'resultados_bipartido.csv')
    print(" Grafo processado com sucesso sem dependências externas!")

if __name__ == "__main__":
    executar()