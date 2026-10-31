# Quantum Commerce — Análise de Sentimento em Reviews
## Trabalho final de Machine Learning (FIAP MBA, turma 4AIER)

**Tema escolhido:** análise de sentimento em reviews, com referência ao Mercado Livre.
**Entrega:** 22/nov/2026 · **Prof.:** Ahirton Lopes (profahirton.lopes@fiap.com.br)
**Repositório:** https://github.com/NahLima/Quantum-Commerce-Store
**Decisão de dataset (31/out/2026):** treinar no Olist real + demonstrar na loja Quantum.

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

O esperado, com dado real, é o comportamento clássico da literatura
para texto curto e pouco dado: a MLP empata ou ganha pouco em F1, e
perde em interpretabilidade, tempo de treino e risco de overfitting.
Se o ganho for pequeno, a recomendação é a LogReg em produção e a MLP
como referência documentada. Se a MLP ganhar com folga no Olist, a
decisão se inverte com evidência — e é por isso que as duas rodam no
mesmo pipeline, não em notebooks separados.

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
| **Olist** — Brazilian E-Commerce Public Dataset (Kaggle) | ~100 mil avaliações reais em PT-BR (2016–2018), com `review_score` 1–5 e texto livre (`review_comment_message`, `review_comment_title`) | Treino e avaliação do modelo. Rótulo por estrelas. Não está no repo (licença Kaggle); baixar e salvar como `backend/data/olist_reviews.csv`, treinar com `python -m ml.train --olist`. |
| **Catálogo Quantum (Figma)** | 50 produtos, 5 categorias, nomes, preços, cores, imagens | Demonstração na loja. Extraído do `App.tsx` do Figma sem inventar nada. |
| **Reviews de demonstração** | 234 avaliações sintéticas em PT-BR, 3–6 por produto, estrelas coerentes com o texto, marcadas como `source=seed` | Termômetro e painel funcionarem na demo. Não são evidência de desempenho — são só o palco. |
| **Golden set manual (a fazer)** | Amostra de avaliações dos produtos Quantum revisada manualmente | Validar a transferência Olist → Quantum (mudança de domínio) antes de afirmar que o modelo funciona na loja. |

Pré-processamento: minúsculas, remoção de stopwords PT-BR, TF-IDF
1–2 gramas. Sem lematização nesta fase (documentado como melhoria
futura de baixo custo).

### 3.3 Pipeline de treinamento

1. Carregar a fonte (`OlistReviewSource`, `CsvReviewSource` ou
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
`python -m ml.train --olist` (Olist, quando o CSV estiver presente).

### 3.4 Métricas de avaliação

Métrica principal: **F1-macro** (as classes são desbalanceadas e a
negativa, minoritária, é a mais importante para a operação).
Apoio: acurácia, precisão e recall por classe, matriz de confusão.

Resultados medidos em 31/out/2026, no dado **sintético** de
demonstração (922 linhas):

| Modelo | Acurácia | F1-macro |
|---|---|---|
| Baseline majoritário | 0,535 | 0,232 |
| TF-IDF + LogReg | 1,000 | 1,000 |
| TF-IDF + MLP | 1,000 | 1,000 |

**Aviso honesto, que faz parte do trabalho:** F1 = 1,0 nos dois
modelos é artefato do dado sintético — os templates de treino e
teste se sobrepõem, então não há generalização real sendo medida.
Esses números provam que o pipeline roda, não que o modelo é
perfeito. Com o Olist real, espera-se F1-macro bem menor (ordem de
0,6–0,75 é típica para sentimento em reviews PT-BR) e é essa queda,
com a matriz de confusão real, que vai virar a discussão do trabalho.
Os 8 testes do backend (`pytest`, 8 passed) e o build do frontend
(`npm run build`, Next 15.5.28) passam; o smoke test ao vivo
confirmou `/predict` (negativo 0,827 num texto de produto quebrado;
positivo 0,967 num elogio) e `POST /reviews` → 201.

### 3.5 Como o resultado é consumido na Quantum

- **Cliente, na página do produto:** termômetro (nota média,
  % positiva/neutra/negativa), "o que gostaram / o que reclamaram"
  (termos de maior coeficiente) e avaliações com selo de sentimento
  e confiança. Igual ao Mercado Livre, na linguagem visual Quantum.
- **Operação, no painel `/ops`:** sentimento por categoria, top
  produtos por share de negativas, alerta > 25%. Ação: revisar
  fornecedor, descrição, lote ou atendimento — e medir se o
  sentimento melhora depois da correção.
- **Produto / marketing:** produtos com sentimento alto e estável
  ganham destaque; produtos com queda súbita entram em revisão
  antes de ganhar tráfego pago.

## 4. Considerações e Potencial de Impacto

### 4.1 Limitações

- **Mudança de domínio.** O modelo treina no Olist (e-commerce
  geral) e é demonstrado na Quantum (catálogo curado específico).
  Sem o golden set manual, não dá para afirmar o desempenho na
  loja — só no Olist.
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

BERT / Transformers em português, aspectos (preço, entrega,
qualidade) em vez de só sentimento global, e, mais adiante, um
assistente que resume as reclamações por produto. Nada disso é base
desta proposta, como pede o enunciado.

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
5. **Treino e métricas:** mostrar `python -m ml.train`, a tabela
   baseline × LogReg × MLP e a matriz de confusão — com o aviso
   do F1 = 1,0 no sintético e o que muda no Olist.
6. **Código:** mostrar `ml/interfaces.py` (o contrato),
   `app/services.py` (a regra) e a tabela SOLID no README.

## Cronograma até 22/11/2026

| Quando | O quê |
|---|---|
| 31/out | Scaffold completo, build e testes passando, push no git (bundle → Mac) |
| Semana 1 (nov) | Baixar Olist do Kaggle, treinar com `--olist`, registrar métricas reais e matriz de confusão |
| Semana 2 | Golden set manual Quantum, validar transferência, ajustar limiar se preciso |
| Semana 3 | Slides/documento final a partir deste plano, ensaio da demo, entrega |

## Referências

- Enunciado da disciplina (Google Doc "Quantum Commerce — Trabalho
  Completo (Turma 4AIER)").
- Scikit-learn Documentation — https://scikit-learn.org/stable/
- Olist Brazilian E-Commerce Public Dataset (Kaggle) —
  https://www.kaggle.com/datasets
- Repositório da disciplina (Demos 1 a 12) —
  https://github.com/ahirtonlopes/Machine-Learning-Foundations-and-Classic-Models
- Projeto Figma (Drive) e este repositório (código, READMEs e
  `backend/ml/artifacts/metrics.json`).
