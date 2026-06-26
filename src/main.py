from collections import deque
import pandas as pd
import grafo_bipartido as gb
import arvoreGerado as mst_mod



def buscar_caminho(MST, origem, destino):
    if origem not in MST or destino not in MST:
        return []

    fila = deque([origem])
    visitados = {origem: None}

    while fila:
        atual = fila.popleft()
        if atual == destino:
            caminho = []
            no = destino
            while no is not None:
                caminho.append(no)
                no = visitados[no]
            caminho.reverse()
            return caminho

        for vizinho in MST.get(atual, {}):
            if vizinho not in visitados:
                visitados[vizinho] = atual
                fila.append(vizinho)

    return []

def calcular_maximo_peso(caminho, MST):
    maximo = 0.0
    for i in range(len(caminho) - 1):
        peso = MST[caminho[i]][caminho[i + 1]]
        if peso > maximo:
            maximo = peso
    return maximo

def componentes_conexos(grafo):
    visitados = set()
    componentes = []

    for no in grafo:
        if no not in visitados:
            componente_atual = []
            fila = deque([no])
            visitados.add(no)

            while fila:
                atual = fila.popleft()
                componente_atual.append(atual)
                for vizinho in grafo.get(atual, {}):
                    if vizinho not in visitados:
                        visitados.add(vizinho)
                        fila.append(vizinho)

            componentes.append(componente_atual)

    return componentes


def detectar_comunidades(MST, k):
    arestas = []
    vistas = set()
    for v in MST:
        for u, peso in MST[v].items():
            chave = tuple(sorted((v, u)))
            if chave not in vistas:
                vistas.add(chave)
                arestas.append((v, u, peso))

    arestas_ordenadas = sorted(arestas, key=lambda e: e[2], reverse=True)
    arestas_para_remover = arestas_ordenadas[:k]

    grafo_fragmentado = {v: dict(vizinhos) for v, vizinhos in MST.items()}
    for v, u, _ in arestas_para_remover:
        grafo_fragmentado[v].pop(u, None)
        grafo_fragmentado[u].pop(v, None)

    return componentes_conexos(grafo_fragmentado)



def pipeline_integracao(caminho_dataset_copom, caminho_retornos_diarios, limiar=3.0, k_comunidades=2):
   
    dados = gb.carregar_dados(caminho_dataset_copom)
    dados = dados.rename(columns={
        'data_reuniao': 'evento',
        'ticker': 'ativo',
        'impacto_pct': 'impacto'
    })
    dados['peso'] = dados['impacto'].abs()

    lista_epicentros, grafo_bip, eventos, ativos = gb.mapear_epicentros(dados)

 
    msts_por_regime = mst_mod.gerar_8_msts(caminho_retornos_diarios)

    tabela_contagio = []
    epicentros_em_ativos = [e for e in lista_epicentros if e in ativos]

    for regime, dados_rede in msts_por_regime.items():
        MST = dados_rede['MST']
        comunidades = detectar_comunidades(MST, k_comunidades)

        for epicentro in epicentros_em_ativos:
            if epicentro not in MST:
                continue
            for ativo in MST:
                if ativo == epicentro:
                    continue
                caminho = buscar_caminho(MST, epicentro, ativo)
                if not caminho:
                    continue
                barreira = calcular_maximo_peso(caminho, MST)
                tabela_contagio.append({
                    'regime': regime,
                    'epicentro': epicentro,
                    'ativo': ativo,
                    'barreira': round(barreira, 4),
                    'comunidades': comunidades
                })

    return tabela_contagio


def exportar_tabela_contagio(tabela_contagio, caminho_saida='discussao_critica_integrada.csv'):
    if not tabela_contagio:
        print("Tabela de contagio vazia - nenhum epicentro coincide com ativos da MST.")
        return

    linhas = [
        {
            'Regime': linha['regime'],
            'Epicentro': linha['epicentro'],
            'Ativo': linha['ativo'],
            'Barreira_Contagio': linha['barreira'],
        }
        for linha in tabela_contagio
    ]

    df = pd.DataFrame(linhas).sort_values(by=['Regime', 'Barreira_Contagio'], ascending=[True, True])
    df.to_csv(caminho_saida, index=False)

    print("--- ANALISE DE DISCUSSAO CRITICA (PipelineIntegracao) ---")
    print(f"Total de pares epicentro-ativo computados: {len(df)}")
    print("Top 5 pares com MENOR barreira de contagio geral:")
    print(df.head(5).to_string(index=False))


if __name__ == "__main__":
    tabela = pipeline_integracao(
        'arestas_final.csv',
        'retornos_diarios_2020_2025.csv',
        limiar=3.0,
        k_comunidades=2
    )
    exportar_tabela_contagio(tabela)