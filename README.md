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

O escopo cobre o período de **janeiro de 2020 a dezembro de 2025**, contemplando quatro fases de política monetária: os cortes emergenciais da pandemia (Selic a 2% a.a.), o ciclo de alta de 2021–2022 (até 13,75%), o ciclo de cortes de 2023–2024 e o novo ciclo de alta iniciado no final de 2024. A análise é restrita a eventos domésticos (decisões do COPOM); eventos internacionais não fazem parte do escopo.

## 2. Abordagem

Usamos duas estruturas de grafo separadas em vez de juntar tudo numa rede só, porque elas respondem perguntas diferentes e trabalham com grandezas que não fazem sentido somar (variação percentual de preço de um lado, coeficiente de correlação do outro).

### 2.1 Grafo 1 — Rede Bipartida Ações × Eventos do COPOM

`G1 = (V1, E1)` é um grafo bipartido ponderado e praticamente completo, com `V1 = A ∪ R`:

- **A** = 23 ações da B3 (NTCO3, JBSS3 e AZUL4 ficaram de fora por falta de dados no `yfinance`), divididas em 8 setores: bancos e finanças, varejo, construção e imobiliário, commodities, utilities, telecomunicações e turismo.
- **R** = 48 reuniões do COPOM entre 2020 e 2025.
- **Peso da aresta** `(aᵢ, rⱼ)`: módulo da variação percentual do preço de fechamento de `aᵢ` entre o pregão anterior (T−1) e o posterior (T+1) à reunião `rⱼ`. A direção da decisão (corte/alta/manutenção) e o sinal da variação ficam salvos como atributo da aresta, mas não entram no peso.
- **Densidade**: 1077 de 1104 arestas possíveis (97,6%) — o que falta é feriado ou falha pontual de dado.

Em cima de G1 aplicamos:

- **Centralidade de grau** — não ajuda muito aqui, já que o grafo é quase completo e todo ativo fica com grau ≈ 48. Serve só de comparação.
- **Centralidade de autovetor** (power iteration) — essa sim é a métrica principal: pondera intensidade da conexão e importância dos vizinhos, e é o que de fato diferencia os ativos mais sensíveis ao conjunto de decisões do COPOM.
- **Emparelhamento de peso máximo** (variante de Edmonds) — acha a associação evento–ativo mais forte sem repetir ativo nem reunião.
- **Cobertura mínima de vértices (Teorema de König)** — construída a partir do emparelhamento sobre o grafo filtrado por um limiar de 3%, dando o menor conjunto de vértices que cobre todas as arestas de impacto relevante.

### 2.2 Grafo 2 — Rede Temporal de Correlação entre Ações

G1 é estático; G2 não. G2 é uma sequência de 8 grafos, um por regime de Selic (`ρ₁` a `ρ₈`), cada regime sendo um período de direção sustentada da taxa (corte, alta ou manutenção), com duração real variando de 31 a 346 pregões.

Para cada regime:

1. calcula a correlação de Pearson `ρᵢⱼ` dos retornos diários entre cada par de ativos;
2. converte correlação em distância pela fórmula de Mantegna (1999): `d_ij = √(2·(1 − ρᵢⱼ))`, que varia de 0 (correlação perfeita) a 2 (anticorrelação perfeita);
3. extrai a MST do grafo completo de distâncias com o algoritmo de Prim, implementado sobre matriz de adjacência — preferimos Prim a Kruskal/Borůvka porque o grafo de correlação é completo, e nesse caso Prim roda em O(V²) sem precisar ordenar todas as arestas;
4. detecta comunidades cortando as k arestas de maior peso (menor similaridade) da MST e tomando os componentes conexos resultantes como grupos.

A correlação usa a série de retornos diários do regime inteiro, e não só os dias de reunião (que seriam poucos demais por regime) nem os preços brutos (que dariam correlação espúria por tendência).

### 2.3 Integração entre as duas camadas

Os ativos identificados como epicentros em G1 (centralidade de autovetor acima da média) são rastreados em cada MST de G2: para cada par epicentro–ativo, calculamos a barreira de contágio como o maior peso ao longo do caminho que liga os dois na árvore (via busca em largura). Barreira baixa indica caminho de alta similaridade, ou seja, mais potencial de um choque se propagar.

### 2.4 Cobertura dos conceitos exigidos

| Conceito de Teoria dos Grafos | Onde é aplicado |
|---|---|
| Centralidade (grau e autovetor) | Grafo 1 |
| Emparelhamento de peso máximo | Grafo 1 |
| Cobertura mínima de vértices (König) | Grafo 1 |
| Árvore Geradora Mínima (Prim) | Grafo 2 |
| Análise de redes temporais / comunidades | Grafo 2 |

## 3. Principais resultados

- **Ativos mais sensíveis** (top-5 por centralidade de autovetor): CVCB3 (turismo), MGLU3, CEAB3, AMER3 (varejo) e MRVE3 (construção civil) — bate com a teoria do canal de crédito: setores dependentes de financiamento ao consumidor amplificam o efeito de variações na Selic.
- **Reunião de maior impacto agregado**: 18/03/2020, coincidindo com o início do choque da COVID-19 na B3 — choques sistêmicos exógenos geram reações mais amplas e simultâneas do que decisões rotineiras de política monetária.
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
│   ├── amostra_bipartido.csv                # amostra ilustrativa do Grafo 1
│   └── discussao_critica_integrada.csv      # tabela de apoio à discussão crítica dos resultados
│
├── src/
│   ├── coleta_precos_diarios.py             # coleta de preços via yfinance e geração dos CSVs de preços/retornos
│   ├── coleta_impacto_selic_v2.py           # cálculo do peso das arestas por reunião
│   ├── grafo_bipartido.py                   # construção do Grafo 1: centralidade de grau/autovetor, epicentros
│   ├── arvoreGerado.py                      # construção do Grafo 2: distância de Mantegna, Prim, comunidades
│   ├── main.py                              # integração: epicentros (G1) × barreira de contágio (G2)
│   ├── visualizar_grafo_bipartido.py        # geração da amostra do grafo bipartido
│   ├── visualizar_grafo_completo_vs_mst.py  # geração grafo completo × MST por regime
│   └── visualizar_grafos_mst.py             # geração das figuras didáticas individuais de cada MST por regime
│
├── results/
│   ├── resultados_bipartido.*                # rankings de centralidade, emparelhamento e cobertura (Grafo 1)
│   ├── mst_Regime_1 … mst_Regime_8.*          # MST extraída por algoritmo de Prim, uma por regime de Selic
│   └── resumo_mst_Regime_1 … resumo_mst_Regime_8.* # resumo estatístico (comunidades, pares estáveis) por regime
│
├── docs/
│   ├── figura_bipartido_amostra.*             # figura 1 do relatório
│   ├── figura_didatica_mst_regime1 … regime8.* # visualizações individuais de cada MST
│   └── figura_mst_regime1 … regime8.*          # visualizações individuais de cada MST
│
├── LICENSE
└── README.md
```

## 5. Execução

Os scripts em `src/` rodam nessa ordem:

1. `coleta_precos_diarios.py` baixa os preços históricos da B3 via `yfinance` e gera os CSVs de preços e retornos diários em `data/`.
2. `coleta_impacto_selic_v2.py` calcula o impacto de cada reunião (T−1 → T+1) cruzando preços e calendário do COPOM, e `grafo_bipartido.py` monta o Grafo 1, calcula as centralidades e identifica os epicentros.
3. `arvoreGerado.py` segmenta os retornos por regime de Selic, calcula a distância de Mantegna, extrai a MST de cada regime via Prim e detecta as comunidades, salvando tudo em `results/`.
4. `main.py` cruza os epicentros do Grafo 1 com as MSTs do Grafo 2 e monta a tabela de barreiras de contágio.
5. Os três scripts `visualizar_*.py` geram as figuras do relatório a partir do que está em `results/` e exportam para `docs/`.

## 6. Referencial teórico

- Mantegna, R. N. (1999). *Hierarchical structure in financial markets*. The European Physical Journal B, 11(1), 193–197.
- Onnela, J.-P., Chakraborti, A., Kaski, K., & Kertész, J. (2003). *Dynamic asset trees and Black Monday*. Physica A, 324(1-2), 247–252.
- Bernanke, B. S. & Kuttner, K. N. (2005). *What explains the stock market's reaction to Federal Reserve policy?* The Journal of Finance, 60(3), 1221–1257.
- Gürkaynak, R. S., Sack, B., & Swanson, E. T. (2005). *The sensitivity of long-term interest rates to economic news*. American Economic Review, 95(1), 425–436.
- Guillaume, J.-L. & Latapy, M. (2006). *Bipartite graphs as models of complex networks*. Physica A, 371(2), 795–813.
- Sorescu, A., Warren, N. L., & Ertekin, L. (2017). *Event study methodology in the marketing literature: an overview*. Journal of the Academy of Marketing Science, 45(2), 186–207.

## 7. Licença

Ver arquivo [LICENSE](LICENSE).
