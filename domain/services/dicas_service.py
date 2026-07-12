"""
Serviço de Dicas do Dia.

Gera de 3 a 4 dicas de segurança/produtividade para o motoboy, combinando
duas fontes:
    1. A condição climática atual (chuva, sol, frio, etc.)
    2. Normas de trânsito e segurança do Detran-SP para motociclistas

Este módulo suporta dois modos de operação:
    - MODO REAL: se `GEMINI_API_KEY` estiver configurada, usa a
      biblioteca `google-generativeai` para gerar as dicas com IA de
      verdade, a partir de um prompt estruturado.
    - MODO SIMULADO (padrão, gratuito): usa um motor de regras local,
      sem nenhuma chamada externa de IA, que combina o clima com um
      banco de dicas pré-escritas alinhadas às normas do Detran-SP.

O modo simulado existe para que o app funcione 100% de graça, sem
exigir que o usuário pague por uma chave de API só para ver as dicas
do dia — e também serve de "fallback" automático caso a chamada real
à IA falhe por qualquer motivo (sem internet, cota excedida, etc.).
"""

import random
from typing import List, Optional

from config.settings import GEMINI_API_KEY, USAR_IA_SIMULADA
from domain.services.weather_service import CondicaoClimatica

# ---------------------------------------------------------------------
# Banco de dicas do MODO SIMULADO, organizado por categoria de clima.
# Todas alinhadas a normas reais e amplamente divulgadas pelo Detran-SP
# para motociclistas (uso de capacete e equipamentos, distância de
# segurança, velocidade compatível com a via, atenção redobrada em
# pista molhada, etc.).
# ---------------------------------------------------------------------
_DICAS_POR_CLIMA = {
    "chuva": [
        "Pista molhada reduz a aderência dos pneus — mantenha distância "
        "de pelo menos 2 segundos do veículo à frente, como recomenda o Detran-SP.",
        "Evite frear bruscamente na chuva. Reduza a velocidade antes das curvas, não durante.",
        "Use capa de chuva de cor clara ou refletiva para aumentar sua visibilidade "
        "para os outros condutores.",
    ],
    "neblina": [
        "Com neblina, use o farol baixo (nunca o alto) para não refletir a luz e "
        "prejudicar ainda mais sua visão, conforme orientação do Detran-SP.",
        "Reduza a velocidade e aumente a distância dos veículos à frente — a "
        "neblina engana a percepção de distância.",
    ],
    "frio": [
        "Vista uma jaqueta corta-vento por baixo do casaco: o frio na pista reduz "
        "os reflexos e pode gerar mais cansaço nas mãos.",
        "Verifique a calibragem dos pneus — o frio reduz a pressão interna, "
        "o que compromete a frenagem.",
    ],
    "sol": [
        "Hidrate-se com frequência: dias de sol forte aumentam o risco de "
        "desidratação e queda de atenção ao longo do turno.",
        "Use protetor solar nas áreas expostas e prefira viseira ou óculos "
        "escuros homologados para reduzir o ofuscamento.",
    ],
    "nublado": [
        "Mesmo sem chuva, o tempo nublado pode escurecer mais cedo — ligue o "
        "farol com antecedência para ser visto por outros veículos.",
    ],
    "neve": [
        "Condições de gelo/neve são raras no Brasil, mas se ocorrerem, evite "
        "rodar: a aderência dos pneus de moto não é projetada para isso.",
    ],
}

# Dicas gerais do Detran-SP, sempre relevantes independente do clima —
# usadas para completar a lista quando há poucas dicas específicas do
# clima do dia, e para reforçar normas básicas de segurança.
_DICAS_GERAIS_DETRAN_SP = [
    "O uso do capacete com viseira é obrigatório em todo o trajeto, mesmo em "
    "distâncias curtas, conforme o Código de Trânsito Brasileiro.",
    "Respeite os corredores apenas nos trechos sinalizados — trafegar entre "
    "veículos fora da faixa permitida é infração gravíssima.",
    "Faça pausas a cada 2 horas de trabalho contínuo: fadiga é uma das "
    "principais causas de acidentes com motociclistas de aplicativo.",
    "Mantenha os equipamentos da moto em dia: freios, pneus e luzes de "
    "sinalização revisados reduzem drasticamente o risco de acidentes.",
]


def _gerar_dicas_modo_simulado(condicao: Optional[CondicaoClimatica]) -> List[str]:
    """
    Motor de regras local que "simula" uma geração por IA: combina as
    dicas específicas do clima atual com dicas gerais do Detran-SP,
    escolhendo uma amostra para não repetir sempre a mesma lista.
    """
    dicas_climaticas = _DICAS_POR_CLIMA.get(condicao.categoria, []) if condicao else []

    quantidade_climaticas = min(2, len(dicas_climaticas))
    selecionadas = random.sample(dicas_climaticas, quantidade_climaticas) if dicas_climaticas else []

    quantidade_gerais = 4 - len(selecionadas)
    selecionadas += random.sample(_DICAS_GERAIS_DETRAN_SP, min(quantidade_gerais, len(_DICAS_GERAIS_DETRAN_SP)))

    return selecionadas


def _montar_prompt(condicao: Optional[CondicaoClimatica]) -> str:
    """Monta o prompt estruturado enviado ao Gemini no modo real."""
    contexto_clima = (
        f"O clima atual é '{condicao.descricao}', com {condicao.temperatura_celsius}°C."
        if condicao else "Não há informação de clima disponível no momento."
    )
    return (
        "Você é um assistente de segurança para motoboys de aplicativo no estado "
        "de São Paulo, Brasil. Gere exatamente 4 dicas curtas (1 frase cada) de "
        "segurança e produtividade para o dia de trabalho, considerando o clima "
        f"informado e as normas de trânsito do Detran-SP. {contexto_clima} "
        "Responda apenas com as 4 dicas, uma por linha, sem numeração."
    )


def _gerar_dicas_modo_real(condicao: Optional[CondicaoClimatica]) -> List[str]:
    """
    Gera dicas usando a API real do Google Gemini, através da biblioteca
    `google-generativeai`. Só é chamado quando GEMINI_API_KEY está
    configurada; qualquer falha aqui é tratada por quem chama esta
    função, que cai automaticamente para o modo simulado.
    """
    import google.generativeai as genai  # import local: só é necessário no modo real

    genai.configure(api_key=GEMINI_API_KEY)
    modelo = genai.GenerativeModel("gemini-1.5-flash")

    resposta = modelo.generate_content(_montar_prompt(condicao))
    linhas = [linha.strip("- •\t ") for linha in resposta.text.strip().split("\n") if linha.strip()]

    return linhas[:4] if linhas else _gerar_dicas_modo_simulado(condicao)


def gerar_dicas_do_dia(condicao: Optional[CondicaoClimatica]) -> List[str]:
    """
    Ponto de entrada único do serviço: decide automaticamente entre o
    modo real (IA) e o modo simulado (regras locais, gratuito), e
    garante que a tela SEMPRE receba uma lista de dicas — nunca uma
    exceção — mesmo que a chamada de IA real falhe por qualquer motivo.
    """
    if USAR_IA_SIMULADA:
        return _gerar_dicas_modo_simulado(condicao)

    try:
        return _gerar_dicas_modo_real(condicao)
    except Exception:
        # Qualquer problema com a IA real (cota, rede, biblioteca ausente)
        # não pode deixar o motoboy sem dicas — caímos para o modo
        # simulado automaticamente, de forma transparente para a tela.
        return _gerar_dicas_modo_simulado(condicao)
