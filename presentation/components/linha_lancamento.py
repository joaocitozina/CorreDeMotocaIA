"""
Linha visual de um lançamento financeiro, usada nas listas roláveis
da tela de Gastos (Pessoais e Manutenção).
"""

from typing import Callable

import customtkinter as ctk

from domain.entities.lancamento import Lancamento
from presentation.components.financeiro_widgets import formatar_moeda
from presentation.theme import colors, styles


class LinhaLancamento(ctk.CTkFrame):
    """
    Uma linha de card mostrando descrição, data e valor de um
    lançamento, com um botão de excluir à direita.
    """

    def __init__(self, master, lancamento: Lancamento, ao_excluir: Callable[[Lancamento], None], **kwargs):
        super().__init__(
            master, fg_color=colors.FUNDO_SECUNDARIO,
            corner_radius=styles.RAIO_CAMPO, **kwargs,
        )

        conteudo = ctk.CTkFrame(self, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=styles.ESPACO_MEDIO, pady=10)
        conteudo.grid_columnconfigure(0, weight=1)

        texto_data = (
            lancamento.data_registro.strftime("%d/%m/%Y às %H:%M")
            if lancamento.data_registro else ""
        )

        ctk.CTkLabel(
            conteudo, text=lancamento.descricao, font=styles.FONTE_TEXTO,
            text_color=colors.TEXTO_PRINCIPAL, anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            conteudo, text=texto_data, font=styles.FONTE_ERRO,
            text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        ).grid(row=1, column=0, sticky="w")

        ctk.CTkLabel(
            conteudo, text=formatar_moeda(lancamento.valor), font=(styles.FONTE_FAMILIA, 15, "bold"),
            text_color=colors.VERMELHO_SALDO_NEGATIVO, anchor="e",
        ).grid(row=0, column=1, rowspan=2, sticky="e", padx=(styles.ESPACO_MEDIO, styles.ESPACO_PEQUENO))

        ctk.CTkButton(
            conteudo, text="✕", width=28, height=28, corner_radius=8,
            fg_color="transparent", hover_color=colors.FUNDO_PRINCIPAL,
            text_color=colors.TEXTO_SECUNDARIO, font=(styles.FONTE_FAMILIA, 13, "bold"),
            command=lambda: ao_excluir(lancamento),
        ).grid(row=0, column=2, rowspan=2, sticky="e")
