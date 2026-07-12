"""
Máscara de telefone aplicada em tempo real a um CTkEntry.

Fica em Presentation (e não em Domain) porque é puramente uma questão
de EXPERIÊNCIA DE DIGITAÇÃO na tela — o Domain já tem seu próprio
validador/formatador (domain/validators/telefone_validator.py), que
continua sendo a fonte oficial de verdade para validar o dado.
"""

import customtkinter as ctk

from domain.validators.telefone_validator import limpar_telefone

TAMANHO_MAXIMO_NUMEROS = 11  # DDD (2) + 9 dígitos do celular


def _montar_texto_progressivo(apenas_numeros: str) -> str:
    """
    Monta a máscara "XX 9XXXX-XXXX" progressivamente, de acordo com a
    quantidade de dígitos que o usuário já digitou — sem exigir que o
    número esteja completo (diferente do formatador oficial do Domain,
    que só formata números já completos e válidos).
    """
    ddd = apenas_numeros[:2]
    parte_1 = apenas_numeros[2:7]
    parte_2 = apenas_numeros[7:11]

    if len(apenas_numeros) <= 2:
        return ddd

    texto = f"{ddd} {parte_1}"
    if parte_2:
        texto += f"-{parte_2}"
    return texto


def aplicar_mascara_telefone(entry: ctk.CTkEntry) -> None:
    """
    Liga um "listener" no campo de telefone que reformata o conteúdo
    a cada tecla digitada, no padrão "XX 9XXXX-XXXX".

    Usamos uma flag de reentrância (`_aplicando_mascara`) porque o
    próprio ato de reescrever o texto do campo (delete + insert)
    dispara novamente o evento <KeyRelease> — sem a flag, isso geraria
    um loop infinito de eventos.
    """
    estado = {"aplicando_mascara": False}

    def _formatar_ao_digitar(_evento=None):
        if estado["aplicando_mascara"]:
            return

        estado["aplicando_mascara"] = True
        try:
            texto_atual = entry.get()
            apenas_numeros = limpar_telefone(texto_atual)[:TAMANHO_MAXIMO_NUMEROS]
            texto_formatado = _montar_texto_progressivo(apenas_numeros)

            if texto_formatado != texto_atual:
                entry.delete(0, "end")
                entry.insert(0, texto_formatado)
                entry.icursor("end")
        finally:
            estado["aplicando_mascara"] = False

    entry.bind("<KeyRelease>", _formatar_ao_digitar)
