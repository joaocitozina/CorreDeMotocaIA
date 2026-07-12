"""
Serviço de consulta à API gratuita da OpenWeatherMap.

Usado na aba "Dicas do Dia" para saber a condição climática atual da
cidade do motoboy e, a partir disso, gerar dicas de segurança mais
relevantes (ex: avisar sobre pista molhada quando está chovendo).
"""

from dataclasses import dataclass

import requests

from config.settings import OPENWEATHER_API_KEY, OPENWEATHER_API_TIMEOUT

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


class ClimaIndisponivelException(Exception):
    """
    Lançada quando não é possível obter o clima — seja por falta de
    chave de API configurada, cidade não encontrada, ou falha de rede.
    A tela trata essa exceção mostrando dicas genéricas mesmo sem o
    dado climático, em vez de travar a aba inteira.
    """
    pass


@dataclass
class CondicaoClimatica:
    """Representa o clima atual de uma cidade, já traduzido para o que a UI precisa."""
    cidade: str
    temperatura_celsius: float
    sensacao_termica_celsius: float
    descricao: str          # ex: "chuva leve", "céu limpo"
    categoria: str          # ex: "chuva", "sol", "nublado", "frio" — usado pelo gerador de dicas
    umidade_percentual: int


def _classificar_categoria(codigo_condicao_ibge: int, temperatura: float) -> str:
    """
    Traduz o código numérico de condição da OpenWeatherMap
    (ex: 2xx = tempestade, 5xx = chuva, 800 = céu limpo) em uma
    categoria simples que o gerador de dicas consegue usar.

    Referência oficial dos códigos: https://openweathermap.org/weather-conditions
    """
    if codigo_condicao_ibge < 600:
        return "chuva"  # grupos 2xx (tempestade), 3xx (garoa) e 5xx (chuva)
    if 600 <= codigo_condicao_ibge < 700:
        return "neve"
    if 700 <= codigo_condicao_ibge < 800:
        return "neblina"
    if codigo_condicao_ibge == 800:
        return "frio" if temperatura <= 18 else "sol"
    return "nublado"  # grupos 80x (nuvens)


def buscar_clima_atual(cidade: str, estado_uf: str) -> CondicaoClimatica:
    """
    Busca o clima atual de uma cidade brasileira.

    Levanta ClimaIndisponivelException se a chave de API não estiver
    configurada — isso é checado ANTES de tentar a chamada HTTP, para
    dar um erro claro em vez de um 401 genérico da API.
    """
    if not OPENWEATHER_API_KEY:
        raise ClimaIndisponivelException(
            "A integração de clima ainda não foi configurada. Defina a variável "
            "de ambiente OPENWEATHER_API_KEY com uma chave gratuita da OpenWeatherMap."
        )

    parametros = {
        "q": f"{cidade},{estado_uf},BR",
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",       # já retorna em Celsius, sem precisar converter
        "lang": "pt_br",
    }

    try:
        resposta = requests.get(BASE_URL, params=parametros, timeout=OPENWEATHER_API_TIMEOUT)
        resposta.raise_for_status()
    except requests.RequestException as erro:
        raise ClimaIndisponivelException(
            f"Não foi possível obter o clima de {cidade} agora. Verifique sua conexão."
        ) from erro

    dados = resposta.json()

    try:
        codigo_condicao = dados["weather"][0]["id"]
        descricao = dados["weather"][0]["description"]
        temperatura = dados["main"]["temp"]
        sensacao = dados["main"]["feels_like"]
        umidade = dados["main"]["humidity"]
    except (KeyError, IndexError) as erro:
        raise ClimaIndisponivelException(
            f"A resposta do serviço de clima veio incompleta para {cidade}."
        ) from erro

    return CondicaoClimatica(
        cidade=cidade,
        temperatura_celsius=round(temperatura, 1),
        sensacao_termica_celsius=round(sensacao, 1),
        descricao=descricao,
        categoria=_classificar_categoria(codigo_condicao, temperatura),
        umidade_percentual=int(umidade),
    )
