"""
Tela de Dicas do Dia.

Busca o clima atual da cidade do motoboy (API OpenWeatherMap) em uma
thread separada e, a partir dele, gera de 3 a 4 dicas de segurança e
produtividade (domain/services/dicas_service.py — modo real com Gemini
ou modo simulado/gratuito, dependendo da configuração do app).
"""

import threading

import customtkinter as ctk

from domain.entities.usuario import Usuario
from domain.services.dicas_service import gerar_dicas_do_dia
from domain.services.weather_service import ClimaIndisponivelException, buscar_clima_atual
from presentation.components.widgets import criar_botao_link, criar_titulo
from presentation.theme import colors, styles

_ICONE_POR_CATEGORIA = {
    "chuva": "🌧️", "neblina": "🌫️", "frio": "🥶",
    "sol": "☀️", "nublado": "☁️", "neve": "❄️",
}


class DicasDoDiaView(ctk.CTkFrame):
    def __init__(self, master, usuario: Usuario):
        super().__init__(master, fg_color=colors.FUNDO_PRINCIPAL)
        self._usuario = usuario

        self._construir_interface()
        self._carregar_clima_e_dicas()

    def _construir_interface(self) -> None:
        area_rolavel = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=colors.LARANJA_VIBRANTE,
            scrollbar_button_hover_color=colors.LARANJA_HOVER,
        )
        area_rolavel.pack(fill="both", expand=True, padx=styles.ESPACO_GRANDE, pady=styles.ESPACO_GRANDE)
        self._area_rolavel = area_rolavel

        linha_titulo = ctk.CTkFrame(area_rolavel, fg_color="transparent")
        linha_titulo.pack(fill="x", pady=(0, styles.ESPACO_GRANDE))

        criar_titulo(linha_titulo, "Dicas do dia").pack(side="left")
        criar_botao_link(linha_titulo, "🔄 Atualizar", self._carregar_clima_e_dicas).pack(side="right")

        self._construir_card_clima(area_rolavel)
        self._construir_lista_dicas(area_rolavel)

    def _construir_card_clima(self, master) -> None:
        self._card_clima = ctk.CTkFrame(master, fg_color=colors.FUNDO_SECUNDARIO, corner_radius=styles.RAIO_CARD)
        self._card_clima.pack(fill="x", pady=(0, styles.ESPACO_GRANDE))

        conteudo = ctk.CTkFrame(self._card_clima, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=styles.ESPACO_MEDIO, pady=styles.ESPACO_MEDIO)

        self._label_clima_principal = ctk.CTkLabel(
            conteudo, text="⏳ Consultando o clima...", font=(styles.FONTE_FAMILIA, 20, "bold"),
            text_color=colors.TEXTO_PRINCIPAL, anchor="w",
        )
        self._label_clima_principal.pack(fill="x")

        self._label_clima_detalhe = ctk.CTkLabel(
            conteudo, text="", font=styles.FONTE_TEXTO,
            text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        )
        self._label_clima_detalhe.pack(fill="x", pady=(4, 0))

    def _construir_lista_dicas(self, master) -> None:
        ctk.CTkLabel(
            master, text="Recomendações para hoje", font=styles.FONTE_LABEL,
            text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        ).pack(fill="x", pady=(0, styles.ESPACO_PEQUENO))

        self._area_dicas = ctk.CTkFrame(master, fg_color="transparent")
        self._area_dicas.pack(fill="x")

    # ------------------------------------------------------------------
    # Carregamento assíncrono (clima depende de rede; dicas não)
    # ------------------------------------------------------------------

    def _carregar_clima_e_dicas(self) -> None:
        self._label_clima_principal.configure(text="⏳ Consultando o clima...")
        self._label_clima_detalhe.configure(text="")

        thread = threading.Thread(target=self._buscar_clima_na_thread, daemon=True)
        thread.start()

    def _buscar_clima_na_thread(self) -> None:
        """
        Executa em background: nunca mexe em widgets diretamente aqui,
        só agenda a atualização via `self.after(0, ...)` na thread principal.
        """
        try:
            condicao = buscar_clima_atual(self._usuario.cidade, self._usuario.estado_uf)
            self.after(0, lambda: self._exibir_clima(condicao))
        except ClimaIndisponivelException as erro:
            self.after(0, lambda: self._exibir_clima_indisponivel(str(erro)))

    def _exibir_clima(self, condicao) -> None:
        icone = _ICONE_POR_CATEGORIA.get(condicao.categoria, "🌤️")
        self._label_clima_principal.configure(
            text=f"{icone} {condicao.temperatura_celsius:.0f}°C em {condicao.cidade}"
        )
        self._label_clima_detalhe.configure(
            text=(
                f"{condicao.descricao.capitalize()} • Sensação de {condicao.sensacao_termica_celsius:.0f}°C "
                f"• Umidade {condicao.umidade_percentual}%"
            )
        )
        self._exibir_dicas(gerar_dicas_do_dia(condicao))

    def _exibir_clima_indisponivel(self, mensagem: str) -> None:
        self._label_clima_principal.configure(text="🌤️ Clima indisponível no momento")
        self._label_clima_detalhe.configure(text=mensagem)
        # Mesmo sem o clima, o motoboy não fica sem nenhuma dica —
        # geramos as recomendações gerais do Detran-SP normalmente.
        self._exibir_dicas(gerar_dicas_do_dia(None))

    def _exibir_dicas(self, dicas) -> None:
        for widget_filho in self._area_dicas.winfo_children():
            widget_filho.destroy()

        for dica in dicas:
            card_dica = ctk.CTkFrame(
                self._area_dicas, fg_color=colors.FUNDO_SECUNDARIO, corner_radius=styles.RAIO_CAMPO,
            )
            card_dica.pack(fill="x", pady=4)

            ctk.CTkLabel(
                card_dica, text=f"💡 {dica}", font=styles.FONTE_TEXTO,
                text_color=colors.TEXTO_PRINCIPAL, anchor="w", justify="left",
                wraplength=560,
            ).pack(fill="x", padx=styles.ESPACO_MEDIO, pady=styles.ESPACO_PEQUENO)
