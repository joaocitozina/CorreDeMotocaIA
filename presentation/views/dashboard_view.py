"""
Tela de Dashboard.

Tela inicial do Core do sistema: mostra o resumo financeiro do
motoboy (ganhos, gastos por categoria e saldo) usando cards e barras
de progresso nativas do CustomTkinter, além de um atalho rápido para
registrar uma nova corrida/ganho sem precisar trocar de tela.
"""

import customtkinter as ctk

from domain.entities.usuario import Usuario
from domain.exceptions.lancamento_exceptions import LancamentoException
from domain.services.financas_service import FinancasService
from presentation.components.financeiro_widgets import BarraProgressoCategoria, CardValor
from presentation.components.widgets import (
    CampoTexto,
    ComboboxCampo,
    criar_botao_primario,
    criar_mensagem_status,
    criar_titulo,
)
from presentation.theme import colors, styles

# Opções padrão de descrição do registro rápido de corrida — trocamos o
# campo de texto livre por um combobox fechado (Etapa 5) para tornar o
# lançamento mais rápido e evitar descrições digitadas de forma
# inconsistente (ex: "corrida ifood", "Corrida IFOOD", "corr. ifood"...).
_OPCOES_DESCRICAO_RAPIDA = [
    "Corrida iFood - Centro",
    "Corrida Particular",
    "Gorjeta",
    "Cancelamento de Pedido",
]


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, usuario: Usuario):
        super().__init__(master, fg_color=colors.FUNDO_PRINCIPAL)

        self._usuario = usuario
        self._financas_service = FinancasService()

        self._construir_interface()
        self._carregar_resumo()

    def _construir_interface(self) -> None:
        area_rolavel = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=colors.LARANJA_VIBRANTE,
            scrollbar_button_hover_color=colors.LARANJA_HOVER,
        )
        area_rolavel.pack(fill="both", expand=True, padx=styles.ESPACO_GRANDE, pady=styles.ESPACO_GRANDE)

        criar_titulo(area_rolavel, f"Olá, {self._usuario.primeiro_nome()} 👋").pack(anchor="w")
        ctk.CTkLabel(
            area_rolavel, text="Aqui está o resumo da sua semana de corridas.",
            font=styles.FONTE_SUBTITULO, text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        ).pack(anchor="w", pady=(0, styles.ESPACO_GRANDE))

        self._construir_cards_resumo(area_rolavel)
        self._construir_grafico_categorias(area_rolavel)
        self._construir_registro_rapido(area_rolavel)

    def _construir_cards_resumo(self, master) -> None:
        linha_cards = ctk.CTkFrame(master, fg_color="transparent")
        linha_cards.pack(fill="x", pady=(0, styles.ESPACO_GRANDE))
        linha_cards.grid_columnconfigure((0, 1, 2), weight=1, uniform="cards")

        self._card_ganhos = CardValor(linha_cards, rotulo="Total ganho")
        self._card_ganhos.grid(row=0, column=0, sticky="ew", padx=(0, styles.ESPACO_PEQUENO))

        self._card_gastos = CardValor(linha_cards, rotulo="Total gasto")
        self._card_gastos.grid(row=0, column=1, sticky="ew", padx=styles.ESPACO_PEQUENO)

        self._card_saldo = CardValor(linha_cards, rotulo="Saldo atual")
        self._card_saldo.grid(row=0, column=2, sticky="ew", padx=(styles.ESPACO_PEQUENO, 0))

    def _construir_grafico_categorias(self, master) -> None:
        card = ctk.CTkFrame(master, fg_color=colors.FUNDO_SECUNDARIO, corner_radius=styles.RAIO_CARD)
        card.pack(fill="x", pady=(0, styles.ESPACO_GRANDE))

        conteudo = ctk.CTkFrame(card, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=styles.ESPACO_MEDIO, pady=styles.ESPACO_MEDIO)

        ctk.CTkLabel(
            conteudo, text="Para onde foi o seu dinheiro", font=styles.FONTE_LABEL,
            text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        ).pack(fill="x", pady=(0, styles.ESPACO_MEDIO))

        self._barra_pessoal = BarraProgressoCategoria(conteudo, "Gastos pessoais", colors.LARANJA_VIBRANTE)
        self._barra_pessoal.pack(fill="x", pady=(0, styles.ESPACO_MEDIO))

        self._barra_manutencao = BarraProgressoCategoria(conteudo, "Manutenção da moto", colors.VERMELHO_SALDO_NEGATIVO)
        self._barra_manutencao.pack(fill="x")

    def _construir_registro_rapido(self, master) -> None:
        card = ctk.CTkFrame(master, fg_color=colors.FUNDO_SECUNDARIO, corner_radius=styles.RAIO_CARD)
        card.pack(fill="x")

        conteudo = ctk.CTkFrame(card, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=styles.ESPACO_MEDIO, pady=styles.ESPACO_MEDIO)

        ctk.CTkLabel(
            conteudo, text="Registrar corrida rápida", font=styles.FONTE_LABEL,
            text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        ).pack(fill="x", pady=(0, styles.ESPACO_PEQUENO))

        linha_campos = ctk.CTkFrame(conteudo, fg_color="transparent")
        linha_campos.pack(fill="x")
        linha_campos.grid_columnconfigure(0, weight=2)
        linha_campos.grid_columnconfigure(1, weight=1)

        self._campo_descricao = ComboboxCampo(
            linha_campos, rotulo="Descrição", valores=_OPCOES_DESCRICAO_RAPIDA,
        )
        self._campo_descricao.grid(row=0, column=0, sticky="ew", padx=(0, styles.ESPACO_PEQUENO))

        self._campo_valor = CampoTexto(linha_campos, rotulo="Valor recebido", placeholder="Ex: 18,50")
        self._campo_valor.grid(row=0, column=1, sticky="ew")

        self._mensagem_status = criar_mensagem_status(conteudo)
        self._mensagem_status.pack(fill="x", pady=(styles.ESPACO_PEQUENO, 0))

        botao_registrar = criar_botao_primario(conteudo, "Registrar ganho", self._tratar_registro_ganho)
        botao_registrar.pack(fill="x", pady=(styles.ESPACO_PEQUENO, 0))

    # ------------------------------------------------------------------
    # Dados
    # ------------------------------------------------------------------

    def _carregar_resumo(self) -> None:
        resumo = self._financas_service.obter_resumo_financeiro(self._usuario.id)

        self._card_ganhos.definir_valor(resumo["total_ganhos"])
        self._card_gastos.definir_valor(resumo["total_gastos"])
        self._card_saldo.definir_valor(resumo["saldo"], colorir_por_sinal=True)

        total_ganhos = resumo["total_ganhos"]
        self._barra_pessoal.atualizar(resumo["total_pessoal"], total_ganhos)
        self._barra_manutencao.atualizar(resumo["total_manutencao"], total_ganhos)

    def _tratar_registro_ganho(self) -> None:
        self._mensagem_status.configure(text="")
        self._campo_descricao.limpar_erro()
        self._campo_valor.limpar_erro()

        try:
            self._financas_service.registrar_ganho(
                usuario_id=self._usuario.id,
                descricao=self._campo_descricao.get(),
                valor_texto=self._campo_valor.get(),
            )
            # O combobox de descrição não precisa ser "limpo" como um
            # campo de texto (delete/insert) — como é uma lista fechada
            # de opções, só voltamos para a primeira opção como padrão,
            # deixando pronto para o próximo registro rápido.
            self._campo_descricao.combobox.set(_OPCOES_DESCRICAO_RAPIDA[0])
            self._campo_valor.entry.delete(0, "end")
            self._carregar_resumo()
        except LancamentoException as erro:
            self._mensagem_status.configure(text=str(erro))
        except Exception:
            self._mensagem_status.configure(
                text="Não foi possível registrar o ganho agora. Tente novamente."
            )
