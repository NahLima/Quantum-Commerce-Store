"""Stopwords em português (lista enxuta, inline — sem dependência de NLTK/spaCy).

Usada pelo TF-IDF em `sentiment.py` / `train.py`. Mantida aqui para o
treino e a inferência usarem exatamente o mesmo pré-processamento.
"""

PT_STOPWORDS = [
    "a", "ao", "aos", "aquela", "aquelas", "aquele", "aqueles", "aquilo",
    "as", "até", "com", "como", "da", "das", "de", "dela", "delas", "dele",
    "deles", "depois", "do", "dos", "e", "ela", "elas", "ele", "eles", "em",
    "entre", "era", "eram", "essa", "essas", "esse", "esses", "esta",
    "estamos", "estas", "estava", "estavam", "este", "estes", "estou",
    "eu", "foi", "foram", "há", "isso", "isto", "já", "lhe", "lhes", "mais",
    "mas", "me", "meu", "meus", "minha", "minhas", "muito", "na", "nas",
    "nem", "no", "nos", "nossa", "nossas", "nosso", "nossos", "num", "numa",
    "não", "o", "os", "ou", "para", "pela", "pelas", "pelo", "pelos",
    "por", "que", "quem", "se", "seja", "sejam", "sem", "seu", "seus",
    "sobre", "sua", "suas", "só", "também", "te", "tem", "têm", "todo",
    "todos", "um", "uma", "umas", "uns", "você", "vocês", "é", "são",
    "ser", "está", "estão", "fui", "vou", "vai", "vou", "era", "foi",
    "quando", "onde", "qual", "quais", "quanto", "quantos", "porque",
    "pois", "então", "ainda", "mesmo", "sempre", "nunca", "bem", "mal",
    "muito", "pouco", "cada", "outro", "outra", "outros", "outras",
    "nada", "tudo", "algum", "alguma", "alguns", "algumas", "nenhum",
    "nenhuma", "esse", "desse", "dessa", "disso", "daqui", "daí", "lá",
    "aqui", "ali", "agora", "hoje", "ontem", "amanhã", "antes", "depois",
]
