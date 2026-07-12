"""
Tela de Ganhos Detalhados.

Mostra, em três abas (Diário / Semanal / Mensal), quanto o motoboy
ganhou em cada aplicativo de entrega — com um gráfico de barras
(Matplotlib, no tema Dark do sistema) e uma listagem detalhada logo
abaixo, cada app com seu ícone e cor simulados.
"""

from typing import Dict

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from domain.entities.usuario import Usuario
from domain.services.financas_service import FinancasService
from presentation.components.financeiro_widgets import formatar_moeda
from presentation.components.widgets import criar_titulo
from presentation.theme import colors, styles
from presentation.theme.icones_aplicativos import obter_cor, obter_icone

_ABAS = (("Diário", "diario"), ("Semanal", "semanal"), ("Mensal", "mensal"))


class GanhosView(ctk.CTkFrame):
    def __init__(self, master, usuario: Usuario):
        super().__init__(master, fg_color=colors.FUNDO_PRINCIPAL)

        self._usuario = usuario
        self._financas_service = FinancasService()
        # Guardamos uma referência de cada canvas do Matplotlib para
        # poder destruí-los explicitamente depois — figuras do Matplotlib
        # não são liberadas automaticamente só porque o widget Tkinter
        # que as contém foi destruído, então fazemos isso na mão para
        # não vazar memória conforme o usuário troca de aba/tela.
        self._canvases_ativos = []

        self._construir_interface()

    def _construir_interface(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=styles.ESPACO_GRANDE, pady=styles.ESPACO_GRANDE)

        criar_titulo(container, "Meus ganhos").pack(anchor="w")
        ctk.CTkLabel(
            container, text="Veja quanto cada aplicativo está rendendo para você.",
            font=styles.FONTE_SUBTITULO, text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        ).pack(anchor="w", pady=(0, styles.ESPACO_MEDIO))

        abas = ctk.CTkTabview(
            container,
            fg_color=colors.FUNDO_SECUNDARIO,
            segmented_button_fg_color=colors.FUNDO_PRINCIPAL,
            segmented_button_selected_color=colors.LARANJA_VIBRANTE,
            segmented_button_selected_hover_color=colors.LARANJA_HOVER,
            segmented_button_unselected_color=colors.FUNDO_PRINCIPAL,
            text_color=colors.TEXTO_PRINCIPAL,
            corner_radius=styles.RAIO_CARD,
        )
        abas.pack(fill="both", expand=True)

        for rotulo, periodo in _ABAS:
            aba = abas.add(rotulo)
            self._construir_conteudo_aba(aba, periodo)

    def _construir_conteudo_aba(self, master, periodo: str) -> None:
        """
        Monta o conteúdo de uma aba (Diário, Semanal ou Mensal): busca
        os ganhos agrupados por app naquele período e desenha o gráfico
        + a listagem detalhada logo abaixo.
        """
        area_rolavel = ctk.CTkScrollableFrame(
            master, fg_color="transparent",
            scrollbar_button_color=colors.LARANJA_VIBRANTE,
            scrollbar_button_hover_color=colors.LARANJA_HOVER,
        )
        area_rolavel.pack(fill="both", expand=True)

        ganhos_por_app = self._financas_service.obter_ganhos_por_app(self._usuario.id, periodo)

        if not ganhos_por_app:
            ctk.CTkLabel(
                area_rolavel, text="Nenhum ganho registrado neste período ainda.",
                font=styles.FONTE_TEXTO, text_color=colors.TEXTO_SECUNDARIO,
            ).pack(pady=styles.ESPACO_GRANDE)
            return

        card_grafico = ctk.CTkFrame(area_rolavel, fg_color=colors.FUNDO_SECUNDARIO, corner_radius=styles.RAIO_CARD)
        card_grafico.pack(fill="x", pady=(0, styles.ESPACO_MEDIO))

        canvas_widget = self._criar_grafico_barras(card_grafico, ganhos_por_app)
        canvas_widget.pack(fill="both", expand=True, padx=styles.ESPACO_PEQUENO, pady=styles.ESPACO_PEQUENO)

        self._construir_listagem_por_app(area_rolavel, ganhos_por_app)

    def _criar_grafico_barras(self, master, ganhos_por_app: Dict[str, float]) -> ctk.CTkBaseClass:
        """
        Gera um gráfico de barras simples (um app por barra) usando
        Matplotlib, já estilizado no tema Dark do sistema, e devolve o
        widget Tkinter pronto para ser posicionado com pack()/grid().

        Usamos `Figure` diretamente (em vez de `matplotlib.pyplot`) —
        assim cada gráfico fica isolado em seu próprio objeto, sem
        depender de um estado global compartilhado do pyplot, o que
        evita vazamento de memória em uma aplicação de longa duração
        como esta, onde o usuário troca de tela repetidamente.
        """
        apps_ordenados = sorted(ganhos_por_app.items(), key=lambda item: item[1], reverse=True)
        nomes_apps = [nome for nome, _ in apps_ordenados]
        valores = [valor for _, valor in apps_ordenados]
        cores_barras = [obter_cor(nome) for nome in nomes_apps]

        figura = Figure(figsize=(5, 3), dpi=100)
        figura.patch.set_facecolor(colors.FUNDO_SECUNDARIO)

        eixo = figura.add_subplot(111)
        eixo.set_facecolor(colors.FUNDO_SECUNDARIO)

        barras = eixo.bar(nomes_apps, valores, color=cores_barras, width=0.55)

        # Estiliza os eixos e textos para combinar com o tema escuro —
        # por padrão o Matplotlib desenha tudo em preto, o que ficaria
        # invisível sobre o nosso fundo grafite.
        eixo.tick_params(axis="x", colors=colors.TEXTO_SECUNDARIO, labelsize=9)
        eixo.tick_params(axis="y", colors=colors.TEXTO_SECUNDARIO, labelsize=9)
        for borda in ("top", "right"):
            eixo.spines[borda].set_visible(False)
        for borda in ("left", "bottom"):
            eixo.spines[borda].set_color(colors.BORDA)

        eixo.set_ylabel("R$", color=colors.TEXTO_SECUNDARIO, fontsize=9)
        eixo.yaxis.grid(True, color=colors.BORDA, linewidth=0.6, alpha=0.6)
        eixo.set_axisbelow(True)

        # Mostra o valor exato em cima de cada barra, facilitando a
        # leitura sem precisar mirar no eixo Y.
        for barra, valor in zip(barras, valores):
            eixo.text(
                barra.get_x() + barra.get_width() / 2, barra.get_height(),
                formatar_moeda(valor), ha="center", va="bottom",
                color=colors.TEXTO_PRINCIPAL, fontsize=8,
            )

        figura.tight_layout()

        canvas = FigureCanvasTkAgg(figura, master=master)
        canvas.draw()
        self._canvases_ativos.append(canvas)

        return canvas.get_tk_widget()

    def _construir_listagem_por_app(self, master, ganhos_por_app: Dict[str, float]) -> None:
        total_periodo = sum(ganhos_por_app.values())
        apps_ordenados = sorted(ganhos_por_app.items(), key=lambda item: item[1], reverse=True)

        for nome_app, valor in apps_ordenados:
            linha = ctk.CTkFrame(master, fg_color=colors.FUNDO_SECUNDARIO, corner_radius=styles.RAIO_CAMPO)
            linha.pack(fill="x", pady=4)

            conteudo = ctk.CTkFrame(linha, fg_color="transparent")
            conteudo.pack(fill="both", expand=True, padx=styles.ESPACO_MEDIO, pady=10)

            icone = obter_icone(nome_app)
            cor = obter_cor(nome_app)
            percentual = (valor / total_periodo * 100) if total_periodo > 0 else 0

            ctk.CTkLabel(
                conteudo, text=f"{icone}  {nome_app}", font=styles.FONTE_TEXTO,
                text_color=colors.TEXTO_PRINCIPAL, anchor="w",
            ).pack(side="left")

            ctk.CTkLabel(
                conteudo, text=f"{percentual:.0f}%", font=styles.FONTE_ERRO,
                text_color=cor, anchor="e",
            ).pack(side="right", padx=(styles.ESPACO_PEQUENO, 0))

            ctk.CTkLabel(
                conteudo, text=formatar_moeda(valor), font=(styles.FONTE_FAMILIA, 15, "bold"),
                text_color=colors.VERDE_SALDO_POSITIVO, anchor="e",
            ).pack(side="right")

    def destruir_recursos_graficos(self) -> None:
        """
        Libera explicitamente as figuras do Matplotlib associadas a
        esta tela. Chamado pelo PainelPrincipalView antes de trocar de
        tela, complementando o destroy() padrão do Tkinter.
        """
        for canvas in self._canvases_ativos:
            figura = canvas.figure
            canvas.get_tk_widget().destroy()
            figura.clf()
        self._canvases_ativos.clear()
