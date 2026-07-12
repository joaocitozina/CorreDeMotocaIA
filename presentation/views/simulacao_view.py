"""
Tela de Simulação.

Permite ao motoboy simular o lucro líquido de um dia de trabalho ANTES
de sair rodando, informando quantas corridas pretende fazer, o valor
médio por corrida e o consumo estimado de combustível.
"""

import customtkinter as ctk

from domain.exceptions.lancamento_exceptions import ValorInvalidoException
from domain.services.simulacao_service import ResultadoSimulacao, simular_dia_de_trabalho
from presentation.components.financeiro_widgets import formatar_moeda
from presentation.components.widgets import CampoTexto, criar_botao_primario, criar_mensagem_status, criar_titulo
from presentation.theme import colors, styles

# Tabela de referência de consumo médio por modelo de moto popular
# entre motoboys de aplicativo — valores aproximados de mercado, só
# para orientar o preenchimento do campo "Consumo da moto (km/l)".
_REFERENCIA_CONSUMO_MOTOS = (
    ("Honda CG 160", "~35 a 40 km/L"),
    ("Honda Biz 125", "~45 a 50 km/L"),
    ("Yamaha YBR 150 Factor", "~38 a 42 km/L"),
    ("Honda XRE 190", "~30 a 35 km/L"),
)


class SimulacaoView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=colors.FUNDO_PRINCIPAL)
        self._construir_interface()

    def _construir_interface(self) -> None:
        area_rolavel = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=colors.LARANJA_VIBRANTE,
            scrollbar_button_hover_color=colors.LARANJA_HOVER,
        )
        area_rolavel.pack(fill="both", expand=True, padx=styles.ESPACO_GRANDE, pady=styles.ESPACO_GRANDE)

        criar_titulo(area_rolavel, "Simule seu dia").pack(anchor="w")
        ctk.CTkLabel(
            area_rolavel,
            text="Descubra quanto vai sobrar no bolso antes de sair para rodar.",
            font=styles.FONTE_SUBTITULO, text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        ).pack(anchor="w", pady=(0, styles.ESPACO_GRANDE))

        card_formulario = ctk.CTkFrame(area_rolavel, fg_color=colors.FUNDO_SECUNDARIO, corner_radius=styles.RAIO_CARD)
        card_formulario.pack(fill="x", pady=(0, styles.ESPACO_GRANDE))

        conteudo = ctk.CTkFrame(card_formulario, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=styles.ESPACO_MEDIO, pady=styles.ESPACO_MEDIO)

        linha_1 = ctk.CTkFrame(conteudo, fg_color="transparent")
        linha_1.pack(fill="x", pady=(0, styles.ESPACO_MEDIO))
        linha_1.grid_columnconfigure((0, 1), weight=1)

        self._campo_corridas = CampoTexto(linha_1, rotulo="Quantidade de corridas", placeholder="Ex: 12")
        self._campo_corridas.grid(row=0, column=0, sticky="ew", padx=(0, styles.ESPACO_PEQUENO))

        self._campo_valor_medio = CampoTexto(linha_1, rotulo="Valor médio por corrida (R$)", placeholder="Ex: 15,00")
        self._campo_valor_medio.grid(row=0, column=1, sticky="ew")

        linha_2 = ctk.CTkFrame(conteudo, fg_color="transparent")
        linha_2.pack(fill="x", pady=(0, styles.ESPACO_MEDIO))
        linha_2.grid_columnconfigure((0, 1, 2), weight=1)

        self._campo_km_rodado = CampoTexto(linha_2, rotulo="KM total rodado", placeholder="Ex: 85")
        self._campo_km_rodado.grid(row=0, column=0, sticky="ew", padx=(0, styles.ESPACO_PEQUENO))

        self._campo_consumo = CampoTexto(linha_2, rotulo="Consumo da moto (km/l)", placeholder="Ex: 35")
        self._campo_consumo.grid(row=0, column=1, sticky="ew", padx=styles.ESPACO_PEQUENO)

        self._campo_preco_combustivel = CampoTexto(linha_2, rotulo="Preço do litro (R$)", placeholder="Ex: 6,10")
        self._campo_preco_combustivel.grid(row=0, column=2, sticky="ew", padx=(styles.ESPACO_PEQUENO, 0))

        self._mensagem_status = criar_mensagem_status(conteudo)
        self._mensagem_status.pack(fill="x", pady=(0, styles.ESPACO_PEQUENO))

        botao_simular = criar_botao_primario(conteudo, "Simular lucro do dia", self._tratar_simulacao)
        botao_simular.pack(fill="x")

        self._construir_resultado(area_rolavel)
        self._construir_tabela_referencia_consumo(area_rolavel)

    def _construir_resultado(self, master) -> None:
        self._card_resultado = ctk.CTkFrame(
            master, fg_color=colors.FUNDO_SECUNDARIO, corner_radius=styles.RAIO_CARD,
        )
        # Começa oculto — só aparece depois da primeira simulação.

        conteudo = ctk.CTkFrame(self._card_resultado, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=styles.ESPACO_MEDIO, pady=styles.ESPACO_MEDIO)

        self._label_lucro_liquido = ctk.CTkLabel(
            conteudo, text="", font=(styles.FONTE_FAMILIA, 30, "bold"), anchor="w",
        )
        self._label_lucro_liquido.pack(fill="x")

        self._label_detalhes = ctk.CTkLabel(
            conteudo, text="", font=styles.FONTE_TEXTO, text_color=colors.TEXTO_SECUNDARIO,
            anchor="w", justify="left",
        )
        self._label_detalhes.pack(fill="x", pady=(styles.ESPACO_PEQUENO, 0))

    def _tratar_simulacao(self) -> None:
        self._mensagem_status.configure(text="")

        try:
            resultado = simular_dia_de_trabalho(
                quantidade_corridas_texto=self._campo_corridas.get(),
                valor_medio_por_corrida_texto=self._campo_valor_medio.get(),
                km_total_rodado_texto=self._campo_km_rodado.get(),
                consumo_km_por_litro_texto=self._campo_consumo.get(),
                preco_litro_combustivel_texto=self._campo_preco_combustivel.get(),
            )
            self._exibir_resultado(resultado)
        except ValorInvalidoException as erro:
            self._mensagem_status.configure(text=str(erro))
        except ZeroDivisionError:
            self._mensagem_status.configure(text="O consumo da moto não pode ser zero.")
        except Exception:
            self._mensagem_status.configure(text="Não foi possível calcular a simulação agora.")

    def _exibir_resultado(self, resultado: ResultadoSimulacao) -> None:
        cor = colors.VERDE_SALDO_POSITIVO if resultado.lucro_liquido >= 0 else colors.VERMELHO_SALDO_NEGATIVO

        self._label_lucro_liquido.configure(
            text=f"Lucro líquido estimado: {formatar_moeda(resultado.lucro_liquido)}",
            text_color=cor,
        )
        self._label_detalhes.configure(
            text=(
                f"Faturamento bruto: {formatar_moeda(resultado.total_bruto)}\n"
                f"Combustível estimado: {resultado.litros_consumidos} L "
                f"({formatar_moeda(resultado.gasto_combustivel)})\n"
                f"Lucro médio por corrida: {formatar_moeda(resultado.lucro_por_corrida)}"
            )
        )

        self._card_resultado.pack(fill="x")

    def _construir_tabela_referencia_consumo(self, master) -> None:
        """
        Frame estático (não interativo) com uma tabela de referência de
        consumo médio por modelo de moto — só para ajudar o motoboy a
        preencher o campo "Consumo da moto (km/l)" do formulário acima
        com um valor realista, caso ele não saiba de cabeça.

        É estático de propósito: não precisa de banco de dados nem de
        lógica nenhuma, é só uma tabela de referência de mercado.
        """
        card = ctk.CTkFrame(master, fg_color=colors.FUNDO_SECUNDARIO, corner_radius=styles.RAIO_CARD)
        card.pack(fill="x", pady=(styles.ESPACO_GRANDE, 0))

        conteudo = ctk.CTkFrame(card, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=styles.ESPACO_MEDIO, pady=styles.ESPACO_MEDIO)

        ctk.CTkLabel(
            conteudo, text="📋 Consumo médio de referência", font=(styles.FONTE_FAMILIA, 15, "bold"),
            text_color=colors.TEXTO_PRINCIPAL, anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            conteudo, text="Não sabe o consumo da sua moto? Use esta tabela como ponto de partida.",
            font=styles.FONTE_ERRO, text_color=colors.TEXTO_SECUNDARIO, anchor="w", justify="left",
        ).pack(fill="x", pady=(0, styles.ESPACO_MEDIO))

        for modelo, faixa_consumo in _REFERENCIA_CONSUMO_MOTOS:
            linha = ctk.CTkFrame(conteudo, fg_color="transparent")
            linha.pack(fill="x", pady=3)

            ctk.CTkLabel(
                linha, text=f"🏍️  {modelo}", font=styles.FONTE_TEXTO,
                text_color=colors.TEXTO_PRINCIPAL, anchor="w",
            ).pack(side="left")

            ctk.CTkLabel(
                linha, text=faixa_consumo, font=(styles.FONTE_FAMILIA, 13, "bold"),
                text_color=colors.LARANJA_VIBRANTE, anchor="e",
            ).pack(side="right")

            # Linha divisória sutil entre um modelo e outro, exceto a
            # última — dá uma organização visual de "tabela" sem
            # precisar montar um Treeview ou grid mais complexo.
            if (modelo, faixa_consumo) != _REFERENCIA_CONSUMO_MOTOS[-1]:
                ctk.CTkFrame(conteudo, fg_color=colors.BORDA, height=1).pack(fill="x", pady=(3, 0))
