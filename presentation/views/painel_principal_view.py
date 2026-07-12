"""
Painel Principal.

É a "casca" do Core do sistema: uma sidebar retrátil à esquerda para
navegação, uma área de conteúdo à direita que troca entre Dashboard /
Gastos / Simulação / Dicas do Dia, e um rodapé fixo na base da janela
inteira com a assinatura do sistema.
"""

from typing import Callable

import customtkinter as ctk

from domain.entities.usuario import Usuario
from presentation.components.sidebar import ItemMenu, Sidebar
from presentation.theme import colors, styles
from presentation.views.dashboard_view import DashboardView
from presentation.views.dicas_view import DicasDoDiaView
from presentation.views.gastos_view import GastosView
from presentation.views.simulacao_view import SimulacaoView


class PainelPrincipalView(ctk.CTkFrame):
    def __init__(self, master, usuario: Usuario, ao_sair: Callable[[], None]):
        super().__init__(master, fg_color=colors.FUNDO_PRINCIPAL)

        self._usuario = usuario
        self._ao_sair = ao_sair
        self._frame_conteudo_atual: ctk.CTkFrame | None = None

        self._construir_interface()
        self._mostrar_dashboard()

    def _construir_interface(self) -> None:
        area_superior = ctk.CTkFrame(self, fg_color="transparent")
        area_superior.pack(fill="both", expand=True)

        itens_menu = [
            ItemMenu("📊", "Dashboard", self._mostrar_dashboard),
            ItemMenu("💰", "Gastos", self._mostrar_gastos),
            ItemMenu("🧮", "Simulação", self._mostrar_simulacao),
            ItemMenu("🌤️", "Dicas do dia", self._mostrar_dicas),
        ]

        self._sidebar = Sidebar(
            area_superior, nome_usuario=self._usuario.primeiro_nome(),
            itens=itens_menu, ao_sair=self._ao_sair,
        )
        self._sidebar.pack(side="left", fill="y")

        self._area_conteudo = ctk.CTkFrame(area_superior, fg_color=colors.FUNDO_PRINCIPAL)
        self._area_conteudo.pack(side="left", fill="both", expand=True)

        self._construir_rodape()

    def _construir_rodape(self) -> None:
        """
        Rodapé fixo do PAINEL PRINCIPAL (base da janela inteira),
        exibido em todas as telas do Core do sistema.
        """
        rodape = ctk.CTkFrame(self, fg_color=colors.FUNDO_SECUNDARIO, height=32, corner_radius=0)
        rodape.pack(side="bottom", fill="x")
        rodape.pack_propagate(False)

        ctk.CTkLabel(
            rodape, text="Criado por Joao vitor barroso A.",
            font=(styles.FONTE_FAMILIA, 11), text_color=colors.TEXTO_SECUNDARIO,
        ).pack(side="right", padx=styles.ESPACO_MEDIO)

    # ------------------------------------------------------------------
    # Navegação entre telas do Core
    # ------------------------------------------------------------------

    def _trocar_conteudo(self, novo_frame: ctk.CTkFrame) -> None:
        if self._frame_conteudo_atual is not None:
            self._frame_conteudo_atual.destroy()
        self._frame_conteudo_atual = novo_frame
        self._frame_conteudo_atual.pack(fill="both", expand=True)

    def _mostrar_dashboard(self) -> None:
        self._trocar_conteudo(DashboardView(self._area_conteudo, usuario=self._usuario))

    def _mostrar_gastos(self) -> None:
        self._trocar_conteudo(GastosView(self._area_conteudo, usuario=self._usuario))

    def _mostrar_simulacao(self) -> None:
        self._trocar_conteudo(SimulacaoView(self._area_conteudo))

    def _mostrar_dicas(self) -> None:
        self._trocar_conteudo(DicasDoDiaView(self._area_conteudo, usuario=self._usuario))
