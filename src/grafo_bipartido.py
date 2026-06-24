import pandas as pd
import networkx as nx

def carregar_dados(caminho_arquivo):
    return pd.read_csv(caminho_arquivo)

def construir_grafo_bipartido(dados):
    grafo = nx.Graph()
    
    eventos = dados['evento'].unique()
    ativos = dados['ativo'].unique()
    
    grafo.add_nodes_from(eventos, bipartite=0)
    grafo.add_nodes_from(ativos, bipartite=1)
    
    for _, linha in dados.iterrows():
        grafo.add_edge(
            linha['evento'], 
            linha['ativo'], 
            peso=linha['peso'],
            impacto=linha['impacto']
        )
        
    return grafo, set(eventos), set(ativos)

def calcular_metricas(grafo, nos_eventos):
    centralidade = nx.bipartite.degree_centrality(grafo, nos_eventos)
    emparelhamento = nx.bipartite.maximum_matching(grafo, top_nodes=nos_eventos)
    cobertura = nx.bipartite.to_vertex_cover(grafo, emparelhamento)
    
    return centralidade, emparelhamento, cobertura

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
        
        # 1. Renomeia as colunas do CSV para o padrão que a função do grafo espera
        dados = dados.rename(columns={
            'data_reuniao': 'evento',
            'ticker': 'ativo',
            'impacto_pct': 'impacto'
        })
        
        # 2. Cria a coluna 'peso' usando o valor absoluto do impacto (módulo)
        dados['peso'] = dados['impacto'].abs()
        
        dados = dados[dados['peso'] > 3.0]
        
    except FileNotFoundError:
        # Dados de teste caso o ficheiro não seja encontrado no diretório
        print(" Ficheiro 'arestas_final.csv' não encontrado. A gerar dados de teste...")
        dados = pd.DataFrame({
            'evento': ['Reuniao_Normal', 'Reuniao_Crise_A', 'Reuniao_Crise_B', 'Pandemia'],
            'ativo': ['ITUB4.SA', 'PETR4.SA', 'MGLU3.SA', 'CVCB3.SA'],
            'impacto': [1.2, -0.5, -5.1, 12.8]
        })
        dados['peso'] = dados['impacto'].abs()
        # Aplica o mesmo filtro nos dados de teste
        dados = dados[dados['peso'] > 3.0]
        
    # Verifica se sobraram dados após o filtro (para evitar que o NetworkX falhe)
    if dados.empty:
        print("❌ O grafo está vazio. Nenhum ativo teve um impacto superior a 3%.")
        return

    # Constrói o grafo apenas com os choques de mercado filtrados
    grafo, eventos, ativos = construir_grafo_bipartido(dados)
    
    # Verifica se a estrutura matemática obedece à regra de um grafo bipartido
    if nx.is_bipartite(grafo):
        cent, emp, cob = calcular_metricas(grafo, eventos)
        exportar_resultados(cent, emp, cob, eventos, 'resultados_bipartido.csv')
        print(" Grafo processado com sucesso!")
        print("O filtro de >3% foi aplicado e eliminou o ruído do mercado.")
        print("Métricas limpas exportadas para 'resultados_bipartido.csv'.")
    else:
        print(" Erro: A estrutura gerada não é um grafo bipartido válido.")

if __name__ == "__main__":
    executar()