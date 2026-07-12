"""
Validação da força da senha.

Regra de negócio: a senha deve ter no mínimo 6 caracteres e conter
pelo menos 1 letra maiúscula, 1 minúscula, 1 número e 1 caractere especial.

Mantemos essa lógica isolada em uma função própria (Single Responsibility)
para que ela possa ser reutilizada tanto no cadastro quanto em uma futura
tela de "alterar senha", sem duplicar código.
"""

import re

from domain.exceptions.auth_exceptions import SenhaInvalidaException

TAMANHO_MINIMO = 6

# Caracteres considerados "especiais" para efeito de validação.
# Mantido como constante para facilitar ajuste futuro (ex: incluir mais símbolos).
CARACTERES_ESPECIAIS = r"!@#$%^&*()\-_=+\[\]{};:,.<>/?\\|~`\"'"


def validar_forca_senha(senha: str) -> None:
    """
    Valida se a senha atende aos critérios mínimos de segurança.

    Não retorna nada em caso de sucesso — apenas lança
    SenhaInvalidaException com a lista de motivos caso alguma regra
    não seja atendida. Esse padrão ("validar ou explodir") deixa o
    código de quem chama mais limpo, sem precisar checar booleanos.
    """
    motivos: list[str] = []

    if senha is None or len(senha) < TAMANHO_MINIMO:
        motivos.append(f"mínimo de {TAMANHO_MINIMO} caracteres")

    if senha and not re.search(r"[A-Z]", senha):
        motivos.append("pelo menos 1 letra maiúscula")

    if senha and not re.search(r"[a-z]", senha):
        motivos.append("pelo menos 1 letra minúscula")

    if senha and not re.search(r"[0-9]", senha):
        motivos.append("pelo menos 1 número")

    if senha and not re.search(f"[{CARACTERES_ESPECIAIS}]", senha):
        motivos.append("pelo menos 1 caractere especial (ex: @, #, !, %)")

    if motivos:
        raise SenhaInvalidaException(motivos)


def calcular_nivel_forca(senha: str) -> str:
    """
    Retorna um rótulo textual do quão forte a senha é: "Fraca", "Média"
    ou "Forte". Usado apenas como feedback visual (ex: barra de força na
    tela de cadastro) — não substitui a validação oficial acima.
    """
    if not senha:
        return "Fraca"

    criterios_atendidos = sum([
        len(senha) >= TAMANHO_MINIMO,
        bool(re.search(r"[A-Z]", senha)),
        bool(re.search(r"[a-z]", senha)),
        bool(re.search(r"[0-9]", senha)),
        bool(re.search(f"[{CARACTERES_ESPECIAIS}]", senha)),
        len(senha) >= 10,  # bônus de comprimento extra
    ])

    if criterios_atendidos >= 5:
        return "Forte"
    if criterios_atendidos >= 3:
        return "Média"
    return "Fraca"
