# Quantum Commerce - Análise de Sentimento em Reviews
## Trabalho final de Machine Learning (FIAP MBA, turma 4AIER)

###  Aluna **Naiara Lima**
### RM:376299

##

**Tema escolhido:** Análise de Sentimento em Reviews de Produtos.

**Prof.:** Ahirton Lopes

**Repositório:** https://github.com/NahLima/Quantum-Commerce-Store

**Decisão de dataset:** treinar no Olist real + B2W + demonstrar na loja Quantum. A escolha entre Olist, Olist+EDA e Olist+B2W foi medida no Colab em 3 versões.

Este documento é o plano escrito do trabalho. A aplicação funcionando
(frontend + backend + banco) está neste mesmo repositório e é a demonstração
da proposta.

---

## 1. Introdução e Problemática

A Quantum Commerce é uma gigante nativa digital do varejo omnicanal,
presente em 12 países, com um catálogo que supera 5 milhões de SKUs. O
problema interno é o "muro da escalabilidade operacional": manter a
qualidade do suporte, a eficiência logística e a personalização de
marketing por métodos tradicionais tornou-se inviável nessa escala.

O desafio endereçado aqui é **transformar o volume de avaliações de
clientes em um termômetro de satisfação por produto e por categoria**.
Hoje, uma avaliação é só um texto solto na página do produto. Ninguém
consegue ler milhares delas, e a operação só percebe um problema quando
ele já virou reclamação em massa, devolução ou queda de venda.

A pergunta que o trabalho responde é: dada uma avaliação em português,
qual é o sentimento dela (positiva, neutra ou negativa), com que
confiança, e o que isso significa, agregado, para cada produto e cada
categoria?

A referência de produto é o Mercado Livre: na página do produto, o
cliente vê a nota média, a distribuição das avaliações e o que os
compradores gostaram e reclamaram. A operação vê o mesmo termômetro e
sabe onde agir primeiro. É exatamente esse fluxo que a demonstração
reproduz, na loja Quantum construída a partir do projeto Figma
(50 produtos, 5 categorias: Tecnologia, Casa, Beleza, Estilo e Outdoor).

Por que esse desafio, e não outro da lista? Porque ele é o que mais
diretamente liga texto não estruturado a decisão: um pico de sentimento
negativo num produto é um sinal acionável no mesmo dia (revisar
fornecedor, descrição, lote ou atendimento), enquanto a avaliação
positiva alimenta destaque e recomendação. E porque ele cabe no escopo
da disciplina: representação clássica de texto (TF-IDF) + regressão
logística ou MLP, sem precisar de Transformers ou modelos generativos.

## 2. Motivação e Justificativa do Modelo

### 2.1 Modelo principal: TF-IDF + Regressão Logística

A avaliação vira vetor com **TF-IDF** (unigramas + bigramas,
`max_features=8000`, `min_df=2`, `sublinear_tf`, stopwords em
português) e é classificada por **regressão logística multinomial**
(`C=4`, `class_weight="balanced"`, 3 classes: positiva, neutra,
negativa, derivadas das estrelas: 1–2 negativa, 3 neutra, 4–5 positiva).

Por que esse é o modelo certo para o problema:

- **Interpretável.** Os coeficientes da regressão logística mostram
  quais termos empurram para positivo ou negativo. Isso importa para
  a operação ("o que reclamaram") e para a banca: dá para explicar
  a decisão, não só acertar.
- **Adequado ao tamanho e à natureza do dado.** Texto curto, em
  português, com vocabulário de e-commerce. TF-IDF captura as
  palavras que importam ("quebrou", "atrasou", "impecável") sem
  precisar de embedding treinado.
- **Barato e rápido.** Treina em segundos em CPU, serve em
  milissegundos, cabe num container pequeno. Numa operação com
  milhões de SKUs, custo de inferência é critério de decisão.
- **Robusto ao desbalanceamento.** Com `class_weight="balanced"` e
  F1-macro como métrica principal, a classe minoritária (neutra e
  negativa) não é ignorada.

### 2.2 Baseline simples

Dois baselines, para provar que o modelo aprendeu alguma coisa:

1. **Majoritário:** prever sempre a classe mais frequente.
2. **Regra por estrelas:** 1–2 negativa, 3 neutra, 4–5 positiva
   (é também a regra que gera os rótulos de treino).

No treino sintético de demonstração (922 linhas, 737 treino / 185
teste), o baseline majoritário ficou em acurácia 0,535 e F1-macro
0,232. Qualquer modelo que não supere isso com folga não está
aprendendo nada. Ver a seção 3.4 para o aviso honesto sobre esses
números.

### 2.3 Comparação: clássico (LogReg) contra rede neural (MLP)

O enunciado pede a comparação clássico contra rede neural, e ela está
implementada: o mesmo TF-IDF alimenta um **MLPClassifier**
(`hidden_layer_sizes=(128,)`, uma camada oculta), treinado e avaliado
no mesmo split, com as mesmas métricas.

Com o Olist real (ver 3.4), o comportamento foi o
clássico da literatura para texto curto e pouco dado: a MLP ganhou
um pouco em acurácia (0,787 contra 0,780) e **perdeu em F1-macro**
(0,600 contra 0,635), por errar muito mais a classe neutra
(recall 0,180 contra 0,354). A recomendação, com evidência, é a
**LogReg em produção** e a MLP como referência documentada — e é
por isso que as duas rodam no mesmo pipeline, não em notebooks
separados.

### 2.4 Alternativas consideradas e descartadas (nesta fase)

| Alternativa | Por que não é a base |
|---|---|
| Léxico de sentimento (lista de palavras) | Usado só como fallback quando não há modelo treinado. Não aprende com os dados e erra negação e contexto ("não é ruim"). |
| Naive Bayes | Baseline válido e rápido, mas a LogReg foi preferida por calibrar melhor as probabilidades e expor coeficientes por termo. |
| Árvores / ensembles | Bons para tabular, ruins para TF-IDF esparso de alta dimensão; perdem para linear neste problema. |
| BERT / Transformers | Fora do escopo da disciplina (tema da próxima) e custo desnecessário para o ganho esperado. Citados só como evolução futura. |
| LLM generativo | Não classifica com custo e latência aceitáveis em escala, e pode inventar rótulo. Fora do escopo. |

## 3. Proposta de Solução

### 3.1 Arquitetura (o que foi construído)

```
Navegador (Next.js 15, React 19, TypeScript, Tailwind v4)
        │  NEXT_PUBLIC_API_URL (http://localhost:8000)
        ▼
FastAPI (Python 3.12) — app/main.py (rotas finas)
        │  services.py (regra) → repositories.py (dados)
        │  ml/predictors.py (SentimentPredictor)
        ▼
Postgres 16 (Docker) — products, reviews, predictions
        │  fallback SQLite local (USE_SQLITE=1) para testes
        ▼
scikit-learn — TF-IDF + LogReg / MLP (ml/artifacts/)
```

- **Frontend (`frontend/`):** migrado do export Figma Make
  (React + Vite) para Next.js App Router, preservando o visual
  (#f7f6f2, #17191c, #3156ff, DM Sans/Manrope). Rotas `/`,
  `/produto/[id]` (termômetro + avaliações + formulário com
  classificação ao vivo) e `/ops` (painel de operações: sentimento
  por categoria e top produtos por share de negativas, com alerta
  quando negativas > 25%). Se a API cair, o site usa os dados
  locais de demonstração e avisa — nunca quebra.
- **Backend (`backend/`):** FastAPI + SQLAlchemy + scikit-learn.
  Endpoints: `GET /health`, `GET /products`, `GET /products/{id}`,
  `GET /products/{id}/sentiment`, `GET /products/{id}/reviews`,
  `POST /predict`, `POST /reviews` (salva + prevê, 201).
- **Banco:** Postgres 16 via `docker-compose.yml` (`db` + `api`).
  Tabelas: `products`, `reviews`, `predictions`. Seed com os
  50 produtos do Figma + 234 avaliações de demonstração
  (130 positivas / 57 neutras / 47 negativas).
- **Código:** orientação a objetos, clean code e SOLID em toda a
  estrutura (ver README da raiz, seção "OOP, SOLID e Clean Code").
  Interfaces `SentimentPredictor` e `ReviewDataSource`: um modelo
  novo ou uma fonte nova entra como uma classe nova, sem editar
  os serviços. `main.py` tem só rotas; `train.py` é só CLI.

### 3.2 Dados necessários

| Fonte | O que é | Uso |
|---|---|---|
| **Olist** — Brazilian E-Commerce Public Dataset (Kaggle) | ~100 mil avaliações reais em PT-BR (2016–2018), com `review_score` 1–5 e texto livre (`review_comment_message`, `review_comment_title`) | Treino e avaliação do modelo. Rótulo por estrelas. Não está no repo (licença Kaggle, ignorado no `.gitignore`); arquivo original na pasta `archive` do Drive, salvo como `backend/data/olist_order_reviews_dataset.csv` (31/out/2026: 42.687 linhas úteis — ver 3.4). |
| **B2W-Reviews01** — Americanas.com (2018), no dataset unificado PT-BR do Kaggle | 132.373 avaliações reais em PT-BR com `rating` 1–5 e texto livre (`review_text`) | Treino oficial junto com o Olist desde 04/nov/2026. Soma 16.315 neutras (4,5× as do Olist) e 35.758 negativas. Não está no repo (CC BY-NC-SA, ignorado no `.gitignore`); arquivo na pasta `archive-v2` do Drive, salvo como `backend/data/b2w_reviews.csv`, treino com `python -m ml.train --olist --b2w` (ver 3.4). |
| **Catálogo Quantum (Figma)** | 50 produtos, 5 categorias, nomes, preços, cores, imagens | Demonstração na loja. Design feito no Figma|
| **Reviews de demonstração** | 234 avaliações sintéticas em PT-BR, 3–6 por produto, estrelas coerentes com o texto, marcadas como `source=seed` | Termômetro e painel funcionarem na demo. Não são evidência de desempenho — são só o palco. |
| **Golden set manual** | 24 avaliações dos produtos Quantum revisadas manualmente, rótulos aprovados pela Naiara (01/nov/2026) | Validar a transferência Olist+B2W → Quantum (mudança de domínio). LogReg oficial: 20/24 = 0,833 (ver 3.4). |

Pré-processamento: minúsculas, remoção de stopwords PT-BR, TF-IDF
1–2 gramas. Sem lematização nesta fase (documentado como melhoria
futura de baixo custo).

### 3.3 Pipeline de treinamento

1. Carregar a fonte (`OlistReviewSource` + `B2WReviewSource`
   combinadas por `CombinedReviewSource`, ou `CsvReviewSource` ou
   `SyntheticReviewSource` — todas implementam `ReviewDataSource`).
2. Rotular por estrelas e limpar textos vazios.
3. Split estratificado 80/20 + validação cruzada.
4. Vetorizar (TF-IDF ajustado só no treino — sem vazamento).
5. Treinar baseline, LogReg e MLP no mesmo split.
6. Avaliar, salvar artefatos em `ml/artifacts/` e registrar
   `metrics.json` + `top_terms.json`.
7. Servir via `POST /predict` (com fallback léxico se não houver
   artefato — a API nunca quebra por falta de modelo).

Comando: `cd backend && python -m ml.train` (sintético) ou
`python -m ml.train --olist` (só Olist, versão 1) ou
`python -m ml.train --olist --b2w` (oficial: Olist + B2W).

### 3.4 Métricas de avaliação

Métrica principal: **F1-macro** (as classes são desbalanceadas e a
negativa, minoritária, é a mais importante para a operação).
Apoio: acurácia, precisão e recall por classe, matriz de confusão.

#### Versão 1 — só Olist (31/out/2026)

Resultados medidos no **Olist real**
(`olist_order_reviews_dataset.csv`, pasta `archive` do Drive;
99.224 linhas, das quais 42.687 com título ou mensagem — 56.537
sem texto foram descartadas; treino 34.149 / teste 8.538):

| Modelo | Acurácia | F1-macro |
|---|---|---|
| Baseline majoritário | 0,657 | 0,264 |
| TF-IDF + LogReg | 0,780 | **0,635** |
| TF-IDF + MLP | 0,787 | 0,600 |

F1 por classe (LogReg): positiva 0,886 (P 0,941 / R 0,837),
negativa 0,761 (P 0,748 / R 0,775), neutra 0,259 (P 0,204 /
R 0,354). A classe neutra é o gargalo — só 3.643 exemplos
(8,5%) e textos ambíguos ("ok", "produto regular"): 292 das
729 neutras do teste foram classificadas como negativas e 179
como positivas. A MLP sofre mais ainda no neutro (F1 0,191,
recall 0,180), o que explica ela ganhar em acurácia e perder
em F1-macro. Matriz de confusão da LogReg (linhas = verdade:
negativa, neutra, positiva): [[1704, 378, 117], [292, 258, 179],
[283, 629, 4698]]. Artefatos em `backend/ml/artifacts/metrics.json`
e `top_terms.json` (ex.: termos positivos "parabéns, amei, rápido,
embalado"; negativos "péssima, ruim, quebrado, demora").

#### As 3 versões do treino — a escolha medida (04/nov/2026)

O Olist sozinho não tinha neutras e negativas suficientes, então
três versões foram comparadas no Colab (notebook
`treino-sentimento-quantum-commerce-v3.ipynb` no Drive), todas com
o mesmo TF-IDF + LogReg e avaliadas **no mesmo teste do Olist**
(8.538 itens) e no golden set (24 itens, domínio Quantum):

| Versão | Treino | F1-macro (teste Olist) | Acurácia | Golden set |
|---|---|---|---|---|
| v1 | Olist (34.149) | 0,635 | 0,780 | 13/24 = 0,542 |
| v2 | Olist + EDA (45.858) | 0,631 | 0,771 | — |
| **v3** | **Olist + B2W (140.047)** | **0,637** | 0,757 | **19/24 = 0,792** |

A v2 (EDA — 1 variante por review neutra/negativa do treino,
troca de posição + remoção de palavra) não ajudou: o TF-IDF é
bag-of-words e trocar a ordem das palavras quase não muda o
vetor. A v3 ganhou nas minoritárias: F1 da negativa 0,761 →
0,788 e recall da neutra 0,354 → 0,433 (F1 0,259 → 0,266), ao
custo de acurácia geral. Um quarto braço, Olist+B2W+Buscapé
(208.039 linhas), foi testado e descartado: F1-macro 0,632 e
golden 17/24 — pior que a v3 nos dois. O SMOTE, testado antes
como braço de comparação, também não resolveu a neutra
(F1-macro 0,639 em 2.000 features, neutra pior). Veredito: **v3
é o treino oficial**.

#### Treino oficial — Olist + B2W (04/nov/2026)

`python -m ml.train --olist --b2w`: o treino faz um único split
80/20 sobre os dados combinados (175.060 linhas com texto;
neutra agora 11,4% do treino, contra 8,5% só no Olist). O teste
aqui é 20% dos dados combinados — por isso os números diferem
da comparação entre versões, cujo teste é só Olist:

| Modelo | Acurácia | F1-macro |
|---|---|---|
| Baseline majoritário | 0,619 | 0,255 |
| TF-IDF + LogReg | 0,743 | **0,662** |
| TF-IDF + MLP | 0,751 | 0,604 |

F1 por classe (LogReg): positiva 0,831, negativa 0,812, neutra
0,344 — a neutra continua sendo o gargalo, mas subiu de 0,259
para 0,344 com o B2W. Matriz de confusão da LogReg (linhas =
verdade: negativa, neutra, positiva): [[7621, 1470, 259],
[871, 2046, 1075], [928, 4399, 16343]]. Artefatos em
`backend/ml/artifacts/metrics.json` e `top_terms.json`.

#### Golden set Quantum — validação na loja (01/nov/2026)

O golden set manual resolve a limitação de domínio (ver 4.1): 24
avaliações novas em PT-BR, escritas para este teste (não copiadas do
seed nem do Olist), ligadas a produtos reais do Figma (ids 1–50),
8 por classe, cobrindo as 5 categorias. Rótulos aprovados pela
Naiara em 01/nov/2026 — os três itens de sentimento misto (G20, G21
e G23) foram mantidos neutros, por decisão dela, e não virados para
positivo para favorecer o modelo. Arquivo `eval/golden_set.csv`;
avaliação reproduzível por `python eval/eval_golden_set.py`
(`--model-dir` aponta os artefatos; os `*.joblib` não são
versionados).

Resultado do LogReg treinado no Olist+B2W (oficial), sem
re-treino: **20/24 = 0,833** (positiva 7/8, negativa 8/8,
neutra 5/8), contra 0,743 de acurácia no teste misto. Os 4
erros: G05 (positiva → neutra, conf. 0,480), G18 (neutra →
negativa, conf. 0,980 — "produto regular, nada demais", que a
v1 acertava), G19 (neutra → positiva, 0,769) e G23 (neutra →
positiva, 0,427). A neutra segue como gargalo (5/8), mas
melhorou muito: G20, G21, G22 e G24 passaram a acertar com o
B2W. Para referência, o mesmo modelo treinado só no Olist
(v1) fazia **13/24 = 0,542** (positiva 6/8, negativa 5/8,
neutra 2/8), contra 0,780 de acurácia no teste do Olist — 5
dos 6 erros de neutra viraram positiva, inclusive dois
neutros claros, G19 ("cumpre o que promete, sem encantar") →
positiva 0,904 e G24 → positiva 0,861 — então o padrão não
dependia dos três rótulos discutíveis. Coerente com o
desbalanceamento do treino v1: 65,7% das 42.687 linhas do
Olist com texto são positivas. Os outros erros da v1:
vocabulário de domínio não visto no Olist (G03 sérum/pele
hidratada → negativa 0,730; G15 "vaza mesmo fechada" →
positiva 0,481) e negativas com defeito virando neutras
(G10, G12) — G03 e G15 acertam na v3, G10 e G12 já
acertavam na v1 e continuam certas.

Só o LogReg foi avaliado — o backend só expõe esse preditor; a MLP
é só artefato de comparação de treino. Discussão que o resultado
alimenta: limiar de decisão para a neutra, e se vale re-treinar com
peso de classe ou ampliar o treino com textos do domínio Quantum
(nada disso feito aqui). Sugestão registrada: ampliar o golden set
para ~40 itens (mais neutras, mais vocabulário de Beleza/Outdoor)
num segundo lote.

Detalhe de método: a MLP do scikit-learn densifica o TF-IDF, então
ela treinou numa subamostra estratificada de 12.000 linhas
(`mlp_n_train` no `metrics.json`); o teste é o mesmo para os três
modelos, então a comparação segue válida. O treino sintético de
demonstração (922 linhas) deu F1 = 1,0 nos dois modelos — artefato
dos templates que se sobrepõem, não resultado real; ele só provou
que o pipeline roda. Os 8 testes do backend (`pytest`, 8 passed) e
o build do frontend (`npm run build`, Next 15.5.28) passam; o smoke
test ao vivo confirmou `/predict` (negativo 0,827 num texto de
produto quebrado; positivo 0,967 num elogio) e `POST /reviews` → 201.

### 3.5 Como o resultado é consumido na Quantum

- **Cliente, na página do produto:** termômetro (nota média,
  % positiva/neutra/negativa), "o que gostaram / o que reclamaram"
  (termos de maior coeficiente) e avaliações com selo de sentimento
  e confiança. Igual ao Mercado Livre, na linguagem visual Quantum.
  Acima da lista, um resumo em prosa das avaliações (`GET
  /products/{id}/summary`): parágrafo estilo Mercado Livre gerado
  por LLM (Gemini) a partir das avaliações do produto, com regras
  de fidelidade (só afirmar o que está nas avaliações; sem inventar
  atributo, preço ou defeito) e cache por produto — sem chave do
  Gemini, ou com poucas avaliações, a página mostra o resumo
  determinístico (contagens + termos), sem quebrar.
- **Operação, no painel `/ops`:** sentimento por categoria, top
  produtos por share de negativas, alerta > 25%. Ação: revisar
  fornecedor, descrição, lote ou atendimento — e medir se o
  sentimento melhora depois da correção.
- **Produto / marketing:** produtos com sentimento alto e estável
  ganham destaque; produtos com queda súbita entram em revisão
  antes de ganhar tráfego pago.

## 4. Considerações e Potencial de Impacto

### 4.1 Limitações

- **Mudança de domínio.** O modelo treina no Olist+B2W (e-commerce
  geral) e é demonstrado na Quantum (catálogo curado específico).
  O golden set manual (01/nov/2026, 24 itens, §3.4) agora permite
  afirmar o desempenho na loja: LogReg oficial 20/24 = 0,833,
  contra 0,743 no teste misto — a transferência funciona, com a
  neutra como gargalo (5/8).
- **Rótulo por estrelas é ruidoso.** Nem toda avaliação 5 estrelas
  é positiva no texto, nem toda 1 estrela é negativa no texto
  (ironia, "chegou rápido mas veio quebrado"). O teto de qualidade
  do modelo é o teto do rótulo.
- **Neutro é difícil.** A classe neutra é a menor e a mais
  ambígua; espera-se o pior recall nela, e é nela que a matriz de
  confusão vai concentrar erro.
- **Texto curto e informal.** Gíria, erro de digitação e abreviação
  limitam o TF-IDF; sem lematização nem embedding, parte do sinal
  se perde.
- **Validação de infra pendente.** Docker e Postgres não foram
  testados nesta VM (não há Docker aqui); a validação do
  `docker compose up` acontece no Mac, antes da apresentação.

### 4.2 Riscos

- **Viés de seleção:** quem avalia não é quem compra em silêncio;
  o termômetro mede quem fala, não todos os clientes.
- **Falso alarme operacional:** um pico de negativas pode ser um
  lote, uma promoção que atraiu outro público, ou um erro de
  classificação — o alerta dispara investigação, não punição
  automática de fornecedor.
- **Drift:** a linguagem muda (novos produtos, novas gírias); o
  modelo precisa de retreino periódico com avaliações novas e
  monitoramento de F1 por categoria.
- **Privacidade:** avaliações podem conter dados pessoais; o
  pipeline não deve expor texto bruto em painéis sem necessidade.

### 4.3 Potencial de valor

- **Detecção precoce:** um produto que cai de 90% para 60% de
  positivas em uma semana aparece no painel antes de virar crise
  de reputação.
- **Priorização com evidência:** em vez de revisar o catálogo
  inteiro, a operação começa pelos 10 produtos com maior share de
  negativas — e mede o efeito da correção no termômetro.
- **Confiança do cliente:** o termômetro transparente (como no
  Mercado Livre) reduz a incerteza de compra e tende a aumentar
  conversão em produtos bem avaliados.
- **Custo baixo:** treino em CPU em segundos, inferência em
  milissegundos, sem dependência de API paga de LLM por avaliação.
  Escala para os 5 milhões de SKUs sem mudar a arquitetura — só
  o volume de dados.

### 4.4 Evolução futura (fora do escopo desta disciplina)

BERT / Transformers em português e aspectos (preço, entrega,
qualidade) em vez de só sentimento global. O resumo das avaliações
por produto já existe como funcionalidade (Gemini + cache, ver
§3.5), e o próximo passo é o experimento documentado em
`notebooks/resumo-avaliacoes-mt5-colab.ipynb`: fine-tunar um modelo
pequeno (mT5-small) em pares (avaliações → resumo) destilados do
Gemini, avaliado por ROUGE + checagem manual de alucinação — se
ficar bom, ele substitui o Gemini; se não, fica a comparação.
Nada disso é base desta proposta, como pede o enunciado: o núcleo
segue sendo o classificador TF-IDF + LogReg/MLP.

---

## Roteiro de demonstração (apresentação)

1. **Home da loja** (`http://localhost:3000`): 50 produtos, 5
   categorias, visual do Figma.
2. **Produto com termômetro:** abrir um produto, mostrar % por
   sentimento, "o que gostaram / reclamaram" e as avaliações com
   selo e confiança.
3. **Classificação ao vivo:** digitar "Produto horrível, veio
   quebrado…" no formulário e mostrar negativo com confiança alta;
   digitar um elogio e mostrar positivo.
4. **Painel `/ops`:** categoria com mais negativas, top produtos,
   alerta > 25%, e a decisão que a operação tomaria.
5. **Treino e métricas:** mostrar `python -m ml.train --olist --b2w`,
   a tabela das 3 versões do treino (v1 Olist, v2 Olist+EDA, v3
   Olist+B2W) e a tabela baseline × LogReg × MLP do treino oficial
   (F1-macro 0,662) com o golden set 20/24 — com a discussão da
   classe neutra como gargalo e do F1 = 1,0 no sintético como
   artefato.
6. **Código:** mostrar `ml/interfaces.py` (o contrato),
   `app/services.py` (a regra) e a tabela SOLID no README.


## Referências

- Scikit-learn Documentation — https://scikit-learn.org/stable/
- Olist Brazilian E-Commerce Public Dataset (Kaggle) —
  https://www.kaggle.com/datasets
- Dataset unificado (Kaggle)  Brazilian Portuguese Sentiment Analysis Datasets - https://www.kaggle.com/datasets/fredericods/ptbr-sentiment-analysis-datasets?select=utlc_apps.csv

- Repositório da disciplina (Demos 1 a 12) —
  https://github.com/ahirtonlopes/Machine-Learning-Foundations-and-Classic-Models

- Algoritmo SMOTE aprimorado para classificação de dados - https://www.nature.com/articles/s41598-025-09506-w

- SMOTE para classificação de dados desbalanceados com Python - https://machinelearningmastery.com/smote-oversampling-for-imbalanced-classification/


- Regressão Logística — Logistic Regression - https://medium.com/@msremigio/regress%C3%A3o-log%C3%ADstica-logistic-regression-997c6259ff9a

- Matriz de confusão - https://www.datacamp.com/pt/tutorial/what-is-a-confusion-matrix-in-machine-learning

-  Text Sentiment Analysis on IMDB Reviews with LSTM | Logistic Regression | Deep Learning Project - https://www.youtube.com/watch?v=uAz2i5CFa0c