"""
Serviço de consulta à API pública do IBGE.

Usado na tela de Cadastro para preencher os campos de Estado e Cidade
sem depender de uma lista estática (que ficaria desatualizada e é
grande demais para manter manualmente). Isolamos toda a comunicação
HTTP aqui para que, se a API do IBGE mudar ou sair do ar, só este
arquivo precise ser ajustado — o resto do sistema nem percebe.
"""

from typing import List, Optional

import requests

from config.settings import IBGE_API_TIMEOUT

BASE_URL = "https://servicodados.ibge.gov.br/api/v1/localidades"


class IBGEServiceException(Exception):
    """
    Lançada quando não é possível falar com a API do IBGE
    (sem internet, timeout, API fora do ar, etc.).

    A tela pode capturar essa exceção especificamente para mostrar
    algo como "Não foi possível carregar as cidades. Verifique sua
    conexão." em vez de travar o cadastro por completo.
    """
    pass


def buscar_estados() -> List[dict]:
    """
    Retorna a lista de estados brasileiros ordenada alfabeticamente.

    Cada item é um dicionário no formato {"sigla": "SP", "nome": "São Paulo"},
    já no formato mais prático para popular um Combobox na tela.
    """
    url = f"{BASE_URL}/estados?orderBy=nome"

    try:
        resposta = requests.get(url, timeout=IBGE_API_TIMEOUT)
        resposta.raise_for_status()
    except requests.RequestException as erro:
        raise IBGEServiceException(
            "Não foi possível carregar a lista de estados. Verifique sua conexão com a internet."
        ) from erro

    dados = resposta.json()
    return [{"sigla": estado["sigla"], "nome": estado["nome"]} for estado in dados]


def buscar_cidades_por_estado(sigla_uf: str) -> List[str]:
    """
    Retorna a lista de nomes de cidades (municípios) de um estado,
    dado sua sigla (ex: "SP", "RJ").

    Recebemos só a sigla, e não o objeto inteiro do estado, para manter
    a assinatura da função simples e desacoplada da tela que a chama.
    """
    if not sigla_uf:
        raise ValueError("A sigla do estado (UF) é obrigatória para buscar as cidades.")

    url = f"{BASE_URL}/estados/{sigla_uf.upper()}/municipios"

    try:
        resposta = requests.get(url, timeout=IBGE_API_TIMEOUT)
        resposta.raise_for_status()
    except requests.RequestException as erro:
        raise IBGEServiceException(
            f"Não foi possível carregar as cidades de {sigla_uf}. Verifique sua conexão com a internet."
        ) from erro

    dados = resposta.json()
    return sorted(cidade["nome"] for cidade in dados)


def validar_cidade_pertence_ao_estado(cidade: str, sigla_uf: str) -> Optional[bool]:
    """
    Confere se a cidade informada realmente existe dentro do estado
    selecionado, evitando inconsistências (ex: usuário digitar uma
    cidade manualmente que não corresponde ao estado escolhido).

    Retorna None se não foi possível consultar a API (falha de rede),
    para que quem chamar decida se quer bloquear o cadastro ou seguir
    em frente de forma tolerante nesse cenário específico.
    """
    try:
        cidades_do_estado = buscar_cidades_por_estado(sigla_uf)
    except IBGEServiceException:
        return None

    return cidade.strip().lower() in [c.lower() for c in cidades_do_estado]
