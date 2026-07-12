"""
Sidebar (menu lateral) retrátil do Painel Principal.

Concentra a navegação entre as telas do Core do sistema (Dashboard,
Gastos, Simulação, Dicas do Dia). É "retrátil" porque o botão de
hambúrguer no topo alterna entre a versão expandida (com texto) e a
versão recolhida (só ícones), economizando espaço em telas menores.
"""

from typing import Callable, List, NamedTuple

import customtkinter as ctk

from presentation.theme import colors, styles


class ItemMenu(NamedTuple):
    """Um item clicável do menu: ícone, rótulo e o que fazer ao clicar."""
    icone: str
    rotulo: str
    comando: Callable[[], None]


class Sidebar(ctk.CTkFrame):
    LARGURA_EXPANDIDA = 220
    LARGURA_RECOLHIDA = 64

    def __init__(self, master, nome_usuario: str, itens: List[ItemMenu], ao_sair: Callable[[], None]):
        super().__init__(
            master, width=self.LARGURA_EXPANDIDA, corner_radius=0,
            fg_color=colors.FUNDO_SECUNDARIO,
        )
        self.pack_propagate(False)

        self._itens = itens
        self._nome_usuario = nome_usuario
        self._ao_sair = ao_sair
        self._expandida = True
        self._botoes_menu: List[ctk.CTkButton] = []
        self._indice_ativo = 0

        self._construir_interface()

    def _construir_interface(self) -> None:
        self._construir_cabecalho()
        self._construir_itens_menu()
        self._construir_rodape_usuario()

    def _construir_cabecalho(self) -> None:
        cabecalho = ctk.CTkFrame(self, fg_color="transparent", height=64)
        cabecalho.pack(fill="x", pady=(styles.ESPACO_MEDIO, styles.ESPACO_GRANDE))
        cabecalho.pack_propagate(False)

        self._botao_hamburguer = ctk.CTkButton(
            cabecalho, text="☰", width=36, height=36,
            fg_color="transparent", hover_color=colors.FUNDO_PRINCIPAL,
            text_color=colors.LARANJA_VIBRANTE, font=(styles.FONTE_FAMILIA, 18, "bold"),
            command=self._alternar_expansao,
        )
        self._botao_hamburguer.pack(side="left", padx=(styles.ESPACO_MEDIO, 0))

        self._label_titulo = ctk.CTkLabel(
            cabecalho, text="Corre dos Motocas", font=(styles.FONTE_FAMILIA, 15, "bold"),
            text_color=colors.TEXTO_PRINCIPAL,
        )
        self._label_titulo.pack(side="left", padx=styles.ESPACO_PEQUENO)

    def _construir_itens_menu(self) -> None:
        area_itens = ctk.CTkFrame(self, fg_color="transparent")
        area_itens.pack(fill="x")

        for indice, item in enumerate(self._itens):
            botao = ctk.CTkButton(
                area_itens,
                text=f"  {item.icone}   {item.rotulo}",
                anchor="w",
                height=styles.ALTURA_BOTAO,
                corner_radius=styles.RAIO_CAMPO,
                fg_color="transparent",
                hover_color=colors.FUNDO_PRINCIPAL,
                text_color=colors.TEXTO_SECUNDARIO,
                font=styles.FONTE_TEXTO,
                command=lambda i=indice: self._selecionar_item(i),
            )
            botao.pack(fill="x", padx=styles.ESPACO_PEQUENO, pady=3)
            self._botoes_menu.append(botao)

        self._destacar_item_ativo()

    def _construir_rodape_usuario(self) -> None:
        """
        Rodapé DA SIDEBAR: nome do usuário logado e botão de sair.
        (Diferente do rodapé do painel principal, que fica na base da
        janela inteira e é responsabilidade da PainelPrincipalView.)
        """
        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", side="bottom", pady=styles.ESPACO_MEDIO)

        self._label_usuario = ctk.CTkLabel(
            rodape, text=f"👤 {self._nome_usuario}", font=styles.FONTE_LABEL,
            text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        )
        self._label_usuario.pack(fill="x", padx=styles.ESPACO_MEDIO, pady=(0, 6))

        self._botao_sair = ctk.CTkButton(
            rodape, text="  🚪   Sair", anchor="w",
            height=38, corner_radius=styles.RAIO_CAMPO,
            fg_color="transparent", hover_color=colors.FUNDO_PRINCIPAL,
            text_color=colors.VERMELHO_SALDO_NEGATIVO, font=styles.FONTE_TEXTO,
            command=self._ao_sair,
        )
        self._botao_sair.pack(fill="x", padx=styles.ESPACO_PEQUENO)

    # ------------------------------------------------------------------
    # Comportamento de expandir/recolher
    # ------------------------------------------------------------------

    def _alternar_expansao(self) -> None:
        self._expandida = not self._expandida

        if self._expandida:
            self.configure(width=self.LARGURA_EXPANDIDA)
            self._label_titulo.pack(side="left", padx=styles.ESPACO_PEQUENO)
            self._label_usuario.pack(fill="x", padx=styles.ESPACO_MEDIO, pady=(0, 6))
            for botao, item in zip(self._botoes_menu, self._itens):
                botao.configure(text=f"  {item.icone}   {item.rotulo}", anchor="w")
            self._botao_sair.configure(text="  🚪   Sair", anchor="w")
        else:
            self.configure(width=self.LARGURA_RECOLHIDA)
            self._label_titulo.pack_forget()
            self._label_usuario.pack_forget()
            for botao, item in zip(self._botoes_menu, self._itens):
                botao.configure(text=item.icone, anchor="center")
            self._botao_sair.configure(text="🚪", anchor="center")

    # ------------------------------------------------------------------
    # Seleção do item ativo
    # ------------------------------------------------------------------

    def _selecionar_item(self, indice: int) -> None:
        self._indice_ativo = indice
        self._destacar_item_ativo()
        self._itens[indice].comando()

    def _destacar_item_ativo(self) -> None:
        """Aplica a cor laranja apenas no item atualmente selecionado."""
        for indice, botao in enumerate(self._botoes_menu):
            if indice == self._indice_ativo:
                botao.configure(fg_color=colors.LARANJA_VIBRANTE, text_color=colors.TEXTO_PRINCIPAL)
            else:
                botao.configure(fg_color="transparent", text_color=colors.TEXTO_SECUNDARIO)
