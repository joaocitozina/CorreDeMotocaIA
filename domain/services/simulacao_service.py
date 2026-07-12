"""
Serviço de Simulação de Ganhos.

Permite ao motoboy simular quanto vai lucrar em um dia de trabalho
ANTES de sair rodando, considerando o gasto de combustível. É uma
calculadora pura — não lê nem escreve no banco, só aplica a fórmula
de negócio sobre os números informados na tela.
"""

from dataclasses import dataclass

from domain.exceptions.lancamento_exceptions import ValorInvalidoException


@dataclass
class ResultadoSimulacao:
    """
    Resultado consolidado de uma simulação de dia de trabalho.

    Mantido como um objeto próprio (em vez de um dicionário solto) para
    que a tela tenha autocomplete e fique explícito o que a simulação
    retorna, sem precisar adivinhar chaves de dicionário.
    """
    total_bruto: float
    litros_consumidos: float
    gasto_combustivel: float
    lucro_liquido: float
    lucro_por_corrida: float


def _converter_para_numero_positivo(valor_texto: str, nome_campo: str) -> float:
    """
    Converte um texto vindo da tela em número, aceitando vírgula ou
    ponto decimal. Reaproveita a mesma exceção humanizada usada nos
    lançamentos financeiros, já que a natureza do erro é idêntica.
    """
    if not valor_texto or not valor_texto.strip():
        raise ValorInvalidoException()

    try:
        numero = float(valor_texto.strip().replace(",", "."))
    except ValueError:
        raise ValorInvalidoException()

    if numero <= 0:
        raise ValorInvalidoException()

    return numero


def simular_dia_de_trabalho(
    quantidade_corridas_texto: str,
    valor_medio_por_corrida_texto: str,
    km_total_rodado_texto: str,
    consumo_km_por_litro_texto: str,
    preco_litro_combustivel_texto: str,
) -> ResultadoSimulacao:
    """
    Calcula o lucro líquido estimado de um dia de trabalho.

    Fórmula:
        total_bruto = corridas × valor médio por corrida
        litros_consumidos = km_total / consumo (km/l)
        gasto_combustivel = litros_consumidos × preço do litro
        lucro_liquido = total_bruto − gasto_combustivel

    Todos os parâmetros chegam como texto (vindos diretamente dos
    campos da tela) e são convertidos/validados aqui, então a
    Presentation não precisa se preocupar em converter nada sozinha.
    """
    quantidade_corridas = _converter_para_numero_positivo(quantidade_corridas_texto, "corridas")
    valor_medio_por_corrida = _converter_para_numero_positivo(valor_medio_por_corrida_texto, "valor médio")
    km_total_rodado = _converter_para_numero_positivo(km_total_rodado_texto, "km rodado")
    consumo_km_por_litro = _converter_para_numero_positivo(consumo_km_por_litro_texto, "consumo")
    preco_litro_combustivel = _converter_para_numero_positivo(preco_litro_combustivel_texto, "preço do combustível")

    total_bruto = quantidade_corridas * valor_medio_por_corrida
    litros_consumidos = km_total_rodado / consumo_km_por_litro
    gasto_combustivel = litros_consumidos * preco_litro_combustivel
    lucro_liquido = total_bruto - gasto_combustivel
    lucro_por_corrida = lucro_liquido / quantidade_corridas

    return ResultadoSimulacao(
        total_bruto=round(total_bruto, 2),
        litros_consumidos=round(litros_consumidos, 2),
        gasto_combustivel=round(gasto_combustivel, 2),
        lucro_liquido=round(lucro_liquido, 2),
        lucro_por_corrida=round(lucro_por_corrida, 2),
    )
