"""
Validação de lançamentos financeiros (ganhos e gastos).
"""

from domain.entities.lancamento import Categoria, Natureza
from domain.exceptions.lancamento_exceptions import (
    CategoriaInvalidaException,
    DescricaoObrigatoriaException,
    ValorInvalidoException,
)

# Mapa das combinações permitidas — garante que "corrida" nunca vire
# uma saída, e que "pessoal"/"manutencao" nunca virem uma entrada.
_CATEGORIAS_POR_NATUREZA = {
    Natureza.ENTRADA: {Categoria.CORRIDA},
    Natureza.SAIDA: {Categoria.PESSOAL, Categoria.MANUTENCAO},
}


def validar_descricao(descricao: str) -> str:
    """Garante que a descrição não está vazia e retorna ela já sem espaços nas pontas."""
    if not descricao or not descricao.strip():
        raise DescricaoObrigatoriaException()
    return descricao.strip()


def validar_valor(valor_texto: str) -> float:
    """
    Converte e valida o valor digitado (que chega como texto da tela).

    Aceita tanto vírgula quanto ponto como separador decimal, já que é
    assim que a maioria dos brasileiros digita valores monetários.
    """
    if not valor_texto or not valor_texto.strip():
        raise ValorInvalidoException()

    texto_normalizado = valor_texto.strip().replace(",", ".")

    try:
        valor = float(texto_normalizado)
    except ValueError:
        raise ValorInvalidoException()

    if valor <= 0:
        raise ValorInvalidoException()

    return round(valor, 2)


def validar_categoria(natureza: Natureza, categoria: Categoria) -> None:
    """Garante que a categoria escolhida é compatível com a natureza do lançamento."""
    categorias_permitidas = _CATEGORIAS_POR_NATUREZA.get(natureza, set())
    if categoria not in categorias_permitidas:
        raise CategoriaInvalidaException()


def validar_lancamento(natureza: Natureza, categoria: Categoria, descricao: str, valor_texto: str):
    """
    Executa todas as validações de um lançamento de uma vez, retornando
    a tupla (descricao_limpa, valor_numerico) pronta para persistir.
    """
    validar_categoria(natureza, categoria)
    descricao_limpa = validar_descricao(descricao)
    valor_numerico = validar_valor(valor_texto)
    return descricao_limpa, valor_numerico
