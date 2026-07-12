"""
Validação e formatação de telefone no padrão brasileiro.

Formato alvo: "XX 9XXXX-XXXX" (DDD + 9º dígito + número), por exemplo
"16 99123-4567". Centralizar essa lógica aqui evita que a máscara da
tela (Presentation) e a validação real (Domain) fiquem desalinhadas.
"""

import re

from domain.exceptions.auth_exceptions import TelefoneInvalidoException

# DDDs válidos no Brasil vão de 11 a 99. Isso ajuda a barrar números
# claramente inválidos (ex: "00" ou "05") que passariam numa regex simples.
DDD_MINIMO = 11
DDD_MAXIMO = 99


def limpar_telefone(telefone: str) -> str:
    """Remove tudo que não for dígito, deixando só os números puros."""
    return re.sub(r"\D", "", telefone or "")


def validar_telefone(telefone: str) -> str:
    """
    Valida um telefone brasileiro e retorna sua versão formatada
    ("XX 9XXXX-XXXX"). Lança TelefoneInvalidoException se o número
    não corresponder a um celular válido com DDD.

    Aceita tanto telefone já formatado quanto só números, o que
    deixa a função tolerante à forma como a tela envia o dado.
    """
    apenas_numeros = limpar_telefone(telefone)

    # Celular brasileiro com DDD tem exatamente 11 dígitos:
    # 2 do DDD + 9 do número (o "9" na frente é obrigatório em celulares).
    if len(apenas_numeros) != 11:
        raise TelefoneInvalidoException()

    ddd = int(apenas_numeros[:2])
    nono_digito = apenas_numeros[2]

    if not (DDD_MINIMO <= ddd <= DDD_MAXIMO):
        raise TelefoneInvalidoException()

    if nono_digito != "9":
        raise TelefoneInvalidoException()

    return formatar_telefone(apenas_numeros)


def formatar_telefone(apenas_numeros: str) -> str:
    """
    Formata uma string de 11 dígitos no padrão "XX 9XXXX-XXXX".

    Mantida separada de validar_telefone() porque a tela também pode
    querer reformatar um número enquanto o usuário ainda está digitando
    (máscara em tempo real), sem precisar validar tudo a cada tecla.
    """
    ddd = apenas_numeros[:2]
    primeira_parte = apenas_numeros[2:7]
    segunda_parte = apenas_numeros[7:11]
    return f"{ddd} {primeira_parte}-{segunda_parte}"
