"""
Exceções customizadas da área financeira (lançamentos de ganhos e gastos).
"""


class LancamentoException(Exception):
    """Classe-base de todas as exceções relacionadas a lançamentos financeiros."""
    pass


class DescricaoObrigatoriaException(LancamentoException):
    """Lançada quando a descrição do lançamento está vazia."""

    def __init__(self):
        super().__init__("Descreva o lançamento antes de salvar (ex: 'Troca de óleo').")


class ValorInvalidoException(LancamentoException):
    """Lançada quando o valor informado não é um número positivo válido."""

    def __init__(self):
        super().__init__("Informe um valor válido e maior que zero (ex: 25,90).")


class CategoriaInvalidaException(LancamentoException):
    """Lançada quando a combinação de natureza + categoria não faz sentido."""

    def __init__(self):
        super().__init__("A categoria selecionada não é válida para este tipo de lançamento.")
