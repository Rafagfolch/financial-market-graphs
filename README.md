# financial-market-graphs

Impacto de Eventos Exógenos sobre o Mercado Financeiro: uma Análise das Decisões do COPOM via Teoria dos Grafos.

Projeto desenvolvido para a disciplina **CMAC03 — Algoritmos em Grafos** (Prof. Rafael Frinhani)

## 1. Objetivo

Os mercados financeiros reagem a eventos exógenos, entre os quais se destacam as decisões de política monetária. O objetivo geral deste projeto é desenvolver uma solução computacional, fundamentada em Teoria dos Grafos, capaz de modelar e analisar o impacto das decisões do Comitê de Política Monetária (COPOM) sobre os ativos do mercado acionário brasileiro (B3), identificando:

- padrões de associação entre eventos (reuniões do COPOM) e ativos;
- padrões de organização estrutural entre os ativos ao longo dos diferentes regimes de juros (Selic).

Especificamente, o projeto busca responder três perguntas:

1. Quais ativos são mais sensíveis ao conjunto de decisões de política monetária do período?
2. Quais associações entre eventos específicos e ativos são as mais expressivas?
3. Como a estrutura de correlação entre os ativos se organiza e se altera ao longo dos diferentes regimes de juros?

O escopo cobre o período de **janeiro de 2020 a dezembro de 2025**, contemplando quatro fases de política monetária: os cortes emergenciais da pandemia (Selic a 2% a.a.), o ciclo de alta de 2021–2022 (até 13,75%), o ciclo de cortes de 2023–2024 e o novo ciclo de alta iniciado no final de 2024. A análise é restrita a eventos domésticos (decisões do COPOM); eventos internacionais não fazem parte do escopo, por decisão do grupo.

## 2. Abordagem

O problema é modelado por meio de **duas estruturas de grafo complementares e independentes**, em vez de uma única rede multi-relacional — escolha justificada pelo fato de as duas estruturas responderem a perguntas distintas e operarem sobre grandezas matematicamente incompatíveis (variação percentual de preço vs. coeficiente de correlação).

### 2.1 Grafo 1 — Rede Bipartida Ações × Eventos do COPOM

Grafo bipartido ponderado e (quase) completo `G1 = (V1, E1)`, com `V1 = A ∪ R`:

- **A** = 23 ações da B3 (após exclusão de NTCO3, JBSS3 e AZUL4 por indisponibilidade persistente de dados no `yfinance`), distribuídas em 8 setores: bancos e finanças, varejo, construção e imobiliário, commodities, utilities, telecomunicações e turismo.
- **R** = 48 reuniões do COPOM realizadas entre 2020 e 2025.
- **Peso da aresta** `(aᵢ, rⱼ)`: módulo da variação percentual do preço de fechamento de `aᵢ` entre o pregão imediatamente anterior (T−1) e o imediatamente posterior (T+1) à reunião `rⱼ`. O sinal da variação e a direção da decisão (corte/alta/manutenção) são salvos como atributos da aresta, mas não entram no cálculo do peso.
- **Densidade**: 1077 de 1104 arestas possíveis (97,6%) — as ausências decorrem de feriados ou falhas pontuais de cobertura de dados.

Algoritmos de Teoria dos Grafos aplicados sobre G1:

- **Centralidade de grau** — pouco informativa, já que o grafo é quase completo (grau ≈ 48 para todo ativo); serve apenas de base de comparação.
- **Centralidade de autovetor** (método das potências / power iteration) — métrica central da análise, pois pondera tanto a intensidade de cada conexão quanto a importância dos vizinhos, identificando os ativos estruturalmente mais sensíveis ao conjunto de decisões do COPOM.
- **Emparelhamento de peso máximo** (variante do algoritmo de Edmonds) — identifica a associação evento–ativo mais forte possível, sem repetir ativo ou reunião.
- **Cobertura mínima de vértices via Teorema de König** — construída a partir do emparelhamento máximo sobre o grafo filtrado por um limiar de relevância de 3%, identificando o menor conjunto de vértices que cobre todas as arestas de impacto significativo.

### 2.2 Grafo 2 — Rede Temporal de Correlação entre Ações

Diferentemente de G1 (estático), G2 é uma **rede temporal**: uma sequência de 8 grafos `G2⁽ᵏ⁾`, um por regime de Selic `ρ₁, ..., ρ₈`, cada um correspondendo a um período de direção sustentada da taxa (corte, alta ou manutenção), com duração definida pela duração real de cada ciclo (de 31 a 346 pregões).

Para cada regime `ρₖ`, o pipeline:

1. calcula a matriz de correlação de Pearson `ρᵢⱼ` dos retornos diários de cada par de ativos no período;
2. converte correlação em distância pela **fórmula de Mantegna (1999)**: `d_ij = √(2·(1 − ρᵢⱼ))`, uma métrica formal que varia entre 0 (correlação perfeita) e 2 (anticorrelação perfeita);
3. extrai a **Árvore Geradora Mínima (MST)** do grafo completo de distâncias via **algoritmo de Prim** (implementado sobre matriz de adjacência — escolhido em vez de Kruskal/Borůvka por o grafo de correlação ser completo, o que dá a Prim complexidade O(V²) sem exigir ordenação global de arestas);
4. aplica uma heurística de **detecção de comunidades** por corte de arestas: remove as k arestas de maior peso (menor similaridade) da MST e toma os componentes conexos resultantes como comunidades.

A correlação é calculada sobre a série contínua de **retornos diários** (não sobre os dias de reunião isoladamente, que seriam poucos por regime, nem sobre preços brutos, que introduziriam correlação espúria por tendência).

### 2.3 Integração entre as duas camadas

Os ativos identificados como **epicentros** em G1 (centralidade de autovetor acima da média) são rastreados em cada MST de G2: para cada par epicentro–ativo, calcula-se a **barreira de contágio** como o maior peso ao longo do caminho que os conecta na árvore (distância ultramétrica subdominante, via busca em largura). Uma barreira baixa indica forte potencial de propagação de choques entre o epicentro e o ativo.

### 2.4 Cobertura dos conceitos exigidos

| Conceito de Teoria dos Grafos | Onde é aplicado |
|---|---|
| Centralidade (grau e autovetor) | Grafo 1 |
| Emparelhamento de peso máximo | Grafo 1 |
| Cobertura mínima de vértices (König) | Grafo 1 |
| Árvore Geradora Mínima (Prim) | Grafo 2 |
| Análise de redes temporais / comunidades | Grafo 2 |

## 3. Principais resultados

- **Ativos mais sensíveis** (top-5 por centralidade de autovetor): CVCB3 (turismo), MGLU3, CEAB3, AMER3 (varejo) e MRVE3 (construção civil) — resultado coerente com a teoria do canal de crédito: setores dependentes de financiamento ao consumidor amplificam o efeito de variações na Selic.
- **Reunião de maior impacto agregado**: 18/03/2020, coincidindo com o início do choque da COVID-19 na B3 — evidenciando que choques sistêmicos exógenos produzem reações mais amplas e simultâneas do que decisões rotineiras de política monetária.
- **Emparelhamento e cobertura**: o emparelhamento máximo satura completamente o lado das ações (todas as 23 participam de algum par forte); a cobertura mínima sob o limiar de 3% resulta nas 23 ações, sem necessidade de incluir reuniões isoladas.
- **Pares estruturalmente estáveis entre regimes**: ITUB4–SANB11 e TIMS3–VIVT3 permanecem na mesma comunidade em todos os 8 regimes, independentemente do ciclo de juros.
- **Reorganização estrutural do mercado**: a liderança topológica de cada MST alterna de forma não linear entre os setores de bancos e construção civil ao longo dos regimes, refutando a hipótese inicial de uma transição setorial simples e ordenada.

Detalhamento completo em `docs/` e no relatório técnico (`Relatorio_CMAC03.pdf`).

## 4. Estrutura do repositório

```
financial-market-graphs/
├── data/
│   ├── precos_diarios_2020_2025.csv         # preços de fechamento diários, B3, 2020-2025
│   ├── retornos_diarios_2020_2025.csv       # retornos diários (formato longo: data, ticker, retorno)
│   ├── retornos_diarios_2020_2025_largo.csv # retornos diários (formato largo)
│   ├── copom_decisoes_2020_2025.csv         # calendário e direção das 48 reuniões do COPOM
│   ├── bipartido_arestas.csv                # arestas do Grafo 1 com pesos calculados
│   ├── arestas_final.csv                    # dataset consolidado final usado nas análises
│   ├── amostra_bipartido.csv                # amostra ilustrativa do Grafo 1 (Figura 1 do relatório)
│   └── discussao_critica_integrada.csv      # tabela de apoio à discussão crítica dos resultados
│
├── src/
│   ├── coleta_precos_diarios.py             # coleta de preços via yfinance e geração dos CSVs de preços/retornos
│   ├── coleta_impacto_selic_v2.py           # cálculo do peso das arestas (impacto % T-1 → T+1) por reunião
│   ├── grafo_bipartido.py                   # construção do Grafo 1: centralidade de grau/autovetor, epicentros
│   ├── arvoreGerado.py                      # construção do Grafo 2: distância de Mantegna, Prim, comunidades
│   ├── main.py                              # pipeline de integração: epicentros (G1) × barreira de contágio (G2)
│   ├── visualizar_grafo_bipartido.py        # geração da Figura 1 (amostra do grafo bipartido)
│   ├── visualizar_grafo_completo_vs_mst.py  # geração das Figuras 2 e 3 (grafo completo × MST por regime)
│   └── visualizar_grafos_mst.py             # geração das figuras didáticas individuais de cada MST por regime
│
├── results/
│   ├── resultados_bipartido.*                # rankings de centralidade, emparelhamento e cobertura (Grafo 1)
│   ├── mst_Regime_1 … mst_Regime_8.*          # MST extraída por algoritmo de Prim, uma por regime de Selic
│   └── resumo_mst_Regime_1 … resumo_mst_Regime_8.* # resumo estatístico (comunidades, pares estáveis) por regime
│
├── docs/
│   ├── figura_bipartido_amostra.*             # Figura 1 do relatório
│   ├── figura_didatica_mst_regime1 … regime8.* # Figuras 2 e 3 do relatório (grafo completo × MST, didáticas)
│   └── figura_mst_regime1 … regime8.*          # visualizações individuais de cada MST
│
├── Relatorio_CMAC03.pdf                       # relatório técnico completo (formato artigo, padrão IMC/UNIFEI)
├── LICENSE
└── README.md
```

## 5. Pipeline de execução

A sequência de execução dos scripts em `src/` segue a ordem das etapas metodológicas:

1. **Coleta de dados** — `coleta_precos_diarios.py` baixa preços históricos da B3 via `yfinance` e gera os CSVs de preços e retornos diários em `data/`.
2. **Construção do Grafo 1** — `coleta_impacto_selic_v2.py` calcula o peso de cada aresta (impacto T−1 → T+1) cruzando preços e calendário do COPOM; `grafo_bipartido.py` constrói o grafo bipartido, calcula centralidade de grau e de autovetor (power iteration) e identifica os ativos epicentros.
3. **Construção do Grafo 2** — `arvoreGerado.py` segmenta os retornos por regime de Selic, calcula a matriz de distância de Mantegna, extrai a MST de cada regime via Prim e detecta comunidades por corte de arestas, salvando os resultados em `results/`.
4. **Integração** — `main.py` cruza os epicentros identificados no Grafo 1 com as MSTs do Grafo 2 e calcula a tabela de barreiras de contágio.
5. **Visualização** — os três scripts `visualizar_*.py` geram as figuras do relatório a partir dos resultados salvos em `results/`, exportando-as para `docs/`.

## 6. Limitações conhecidas

- **Causalidade**: os resultados são associações estruturais, não relações causais — a variação de preço em torno de uma reunião do COPOM pode refletir fatores simultâneos (câmbio, commodities, notícias corporativas), não isolados pela metodologia.
- **Grafo 1 quase completo**: limita a utilidade da centralidade de grau e da cobertura de vértices isoladamente, o que motivou o uso de centralidade de autovetor como métrica complementar.
- **Regimes curtos**: o Regime 6 (31 pregões) produz estimativas de correlação menos robustas que regimes mais longos, como o Regime 3 (346 pregões).
- **Dados faltantes**: SMFT3 e IGTI11 não possuem observações nos Regimes 1 e 2 (IPO posterior); um bug de preenchimento de dados ausentes com zero (em vez de exclusão) foi identificado e corrigido durante o desenvolvimento, exigindo revalidação das 8 árvores.

## 7. Referencial teórico

- Mantegna, R. N. (1999). *Hierarchical structure in financial markets*. The European Physical Journal B, 11(1), 193–197.
- Onnela, J.-P., Chakraborti, A., Kaski, K., & Kertész, J. (2003). *Dynamic asset trees and Black Monday*. Physica A, 324(1-2), 247–252.
- Bernanke, B. S. & Kuttner, K. N. (2005). *What explains the stock market's reaction to Federal Reserve policy?* The Journal of Finance, 60(3), 1221–1257.
- Gürkaynak, R. S., Sack, B., & Swanson, E. T. (2005). *The sensitivity of long-term interest rates to economic news*. American Economic Review, 95(1), 425–436.
- Guillaume, J.-L. & Latapy, M. (2006). *Bipartite graphs as models of complex networks*. Physica A, 371(2), 795–813.
- Sorescu, A., Warren, N. L., & Ertekin, L. (2017). *Event study methodology in the marketing literature: an overview*. Journal of the Academy of Marketing Science, 45(2), 186–207.

## 8. Licença

Ver arquivo [LICENSE](LICENSE).
