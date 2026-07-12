"""
Constantes de estilo (tipografia, espaçamento e formato) do tema Dark.

Complementa `colors.py`. Manter esses valores aqui evita "números
mágicos" espalhados nas views e garante que todas as telas do app
tenham a mesma identidade visual sem esforço extra do desenvolvedor.
"""

# Família de fonte usada em todo o app. "Segoe UI" é nativa do Windows
# (ambiente alvo do projeto) e tem ótima legibilidade em telas escuras.
FONTE_FAMILIA = "Segoe UI"

FONTE_TITULO = (FONTE_FAMILIA, 26, "bold")
FONTE_SUBTITULO = (FONTE_FAMILIA, 14)
FONTE_LABEL = (FONTE_FAMILIA, 13)
FONTE_TEXTO = (FONTE_FAMILIA, 14)
FONTE_BOTAO = (FONTE_FAMILIA, 15, "bold")
FONTE_ERRO = (FONTE_FAMILIA, 12)
FONTE_LINK = (FONTE_FAMILIA, 13, "underline")

# Raio de borda arredondado — aplicado em botões, campos e cards para
# reforçar a estética "moderna" pedida no briefing.
RAIO_BOTAO = 22
RAIO_CAMPO = 10
RAIO_CARD = 16

# Alturas padrão dos componentes interativos, para manter tudo alinhado
ALTURA_ENTRADA = 44
ALTURA_BOTAO = 46
ALTURA_COMBOBOX = 44

# Espaçamentos reutilizados no grid/pack das telas
ESPACO_PEQUENO = 6
ESPACO_MEDIO = 14
ESPACO_GRANDE = 24

# Largura padrão do "card" central de login/cadastro
LARGURA_CARD = 380
