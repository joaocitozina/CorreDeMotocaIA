"""
Widgets reutilizáveis do tema Dark/Laranja.

Concentrar a criação desses componentes aqui evita repetir a mesma
configuração de cor/fonte/borda em cada tela (Login, Cadastro, e as
telas futuras de Dashboard, Corridas, etc.), seguindo o princípio DRY.
"""

from typing import Callable, Optional

import customtkinter as ctk

from presentation.theme import colors, styles


class CampoTexto(ctk.CTkFrame):
    """
    Campo de formulário completo: label acima, entrada de texto e uma
    linha de erro abaixo (invisível até `exibir_erro()` ser chamado).

    Empacotar label + entry + erro num único componente evita que cada
    tela precise gerenciar manualmente o posicionamento da mensagem de
    erro toda vez que uma validação falha.
    """

    def __init__(
        self,
        master,
        rotulo: str,
        placeholder: str = "",
        mostrar_como_senha: bool = False,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._label = ctk.CTkLabel(
            self, text=rotulo, font=styles.FONTE_LABEL,
            text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        )
        self._label.pack(fill="x", pady=(0, 4))

        self.entry = ctk.CTkEntry(
            self,
            placeholder_text=placeholder,
            height=styles.ALTURA_ENTRADA,
            corner_radius=styles.RAIO_CAMPO,
            fg_color=colors.FUNDO_SECUNDARIO,
            border_color=colors.BORDA,
            text_color=colors.TEXTO_PRINCIPAL,
            font=styles.FONTE_TEXTO,
            show="•" if mostrar_como_senha else "",
        )
        self.entry.pack(fill="x")

        self._label_erro = ctk.CTkLabel(
            self, text="", font=styles.FONTE_ERRO,
            text_color=colors.VERMELHO_SALDO_NEGATIVO, anchor="w",
        )
        self._label_erro.pack(fill="x", pady=(2, 0))

    def get(self) -> str:
        """Atalho para obter o texto digitado, já sem espaços nas pontas."""
        return self.entry.get().strip()

    def exibir_erro(self, mensagem: str) -> None:
        """Mostra uma mensagem de erro abaixo do campo e destaca a borda em vermelho."""
        self._label_erro.configure(text=mensagem)
        self.entry.configure(border_color=colors.VERMELHO_SALDO_NEGATIVO)

    def limpar_erro(self) -> None:
        """Remove qualquer mensagem de erro e devolve a borda à cor padrão."""
        self._label_erro.configure(text="")
        self.entry.configure(border_color=colors.BORDA)


class ComboboxCampo(ctk.CTkFrame):
    """
    Mesma ideia do CampoTexto, mas para um CTkComboBox (usado nos
    seletores de Estado e Cidade, alimentados pela API do IBGE).
    """

    def __init__(self, master, rotulo: str, valores: Optional[list] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._label = ctk.CTkLabel(
            self, text=rotulo, font=styles.FONTE_LABEL,
            text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        )
        self._label.pack(fill="x", pady=(0, 4))

        self.combobox = ctk.CTkComboBox(
            self,
            values=valores or ["Carregando..."],
            height=styles.ALTURA_COMBOBOX,
            corner_radius=styles.RAIO_CAMPO,
            fg_color=colors.FUNDO_SECUNDARIO,
            border_color=colors.BORDA,
            button_color=colors.LARANJA_VIBRANTE,
            button_hover_color=colors.LARANJA_HOVER,
            dropdown_fg_color=colors.FUNDO_SECUNDARIO,
            dropdown_hover_color=colors.FUNDO_PRINCIPAL,
            text_color=colors.TEXTO_PRINCIPAL,
            font=styles.FONTE_TEXTO,
            state="readonly",
        )
        self.combobox.pack(fill="x")

        self._label_erro = ctk.CTkLabel(
            self, text="", font=styles.FONTE_ERRO,
            text_color=colors.VERMELHO_SALDO_NEGATIVO, anchor="w",
        )
        self._label_erro.pack(fill="x", pady=(2, 0))

    def get(self) -> str:
        return self.combobox.get().strip()

    def definir_valores(self, valores: list) -> None:
        """Atualiza a lista de opções do combobox (ex: após resposta da API do IBGE)."""
        self.combobox.configure(values=valores)
        if valores:
            self.combobox.set(valores[0])

    def exibir_erro(self, mensagem: str) -> None:
        self._label_erro.configure(text=mensagem)
        self.combobox.configure(border_color=colors.VERMELHO_SALDO_NEGATIVO)

    def limpar_erro(self) -> None:
        self._label_erro.configure(text="")
        self.combobox.configure(border_color=colors.BORDA)


def criar_titulo(master, texto: str) -> ctk.CTkLabel:
    """Título principal da tela (ex: 'Bem-vindo de volta')."""
    return ctk.CTkLabel(
        master, text=texto, font=styles.FONTE_TITULO,
        text_color=colors.TEXTO_PRINCIPAL, anchor="w",
    )


def criar_subtitulo(master, texto: str) -> ctk.CTkLabel:
    """Texto de apoio abaixo do título (ex: 'Entre para continuar')."""
    return ctk.CTkLabel(
        master, text=texto, font=styles.FONTE_SUBTITULO,
        text_color=colors.TEXTO_SECUNDARIO, anchor="w",
    )


def criar_botao_primario(master, texto: str, comando: Callable) -> ctk.CTkButton:
    """
    Botão de ação principal: fundo laranja vibrante, cantos bem
    arredondados — exatamente como pedido no briefing visual do app.
    """
    return ctk.CTkButton(
        master,
        text=texto,
        command=comando,
        height=styles.ALTURA_BOTAO,
        corner_radius=styles.RAIO_BOTAO,
        fg_color=colors.LARANJA_VIBRANTE,
        hover_color=colors.LARANJA_HOVER,
        text_color=colors.TEXTO_PRINCIPAL,
        font=styles.FONTE_BOTAO,
    )


def criar_botao_link(master, texto: str, comando: Callable) -> ctk.CTkButton:
    """
    Botão "fantasma" (sem fundo), usado para ações secundárias como
    "Não tem conta? Cadastre-se" — visualmente leve, mas ainda clicável.
    """
    return ctk.CTkButton(
        master,
        text=texto,
        command=comando,
        height=28,
        fg_color="transparent",
        hover_color=colors.FUNDO_SECUNDARIO,
        text_color=colors.LARANJA_VIBRANTE,
        font=styles.FONTE_LINK,
    )


def criar_mensagem_status(master) -> ctk.CTkLabel:
    """
    Label genérica para mensagens de erro/sucesso de nível de tela
    (ex: 'Telefone ou senha incorretos'), diferente dos erros por campo.
    """
    return ctk.CTkLabel(
        master, text="", font=styles.FONTE_ERRO,
        text_color=colors.VERMELHO_SALDO_NEGATIVO,
        anchor="w", justify="left", wraplength=styles.LARGURA_CARD,
    )
