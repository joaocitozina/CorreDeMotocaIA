"""
Tela de Gastos.

Permite registrar e visualizar dois tipos de despesa do motoboy:
gastos PESSOAIS (alimentação, aluguel, etc.) e gastos de MANUTENÇÃO
da moto (óleo, pneus, revisão). Usamos um CTkTabview para separar as
duas categorias sem precisar de duas telas totalmente distintas.
"""

from typing import Callable, List

import customtkinter as ctk

from domain.entities.lancamento import Lancamento
from domain.entities.usuario import Usuario
from domain.exceptions.lancamento_exceptions import LancamentoException
from domain.services.financas_service import FinancasService
from presentation.components.linha_lancamento import LinhaLancamento
from presentation.components.widgets import CampoTexto, criar_botao_primario, criar_mensagem_status, criar_titulo
from presentation.theme import colors, styles


class GastosView(ctk.CTkFrame):
    def __init__(self, master, usuario: Usuario):
        super().__init__(master, fg_color=colors.FUNDO_PRINCIPAL)

        self._usuario = usuario
        self._financas_service = FinancasService()

        self._construir_interface()

    def _construir_interface(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=styles.ESPACO_GRANDE, pady=styles.ESPACO_GRANDE)

        criar_titulo(container, "Meus gastos").pack(anchor="w")
        ctk.CTkLabel(
            container, text="Controle o que sai do seu bolso, separado por categoria.",
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

        aba_pessoal = abas.add("Pessoais")
        aba_manutencao = abas.add("Manutenção")

        self._painel_pessoal = _PainelCategoriaGasto(
            aba_pessoal,
            ao_registrar=self._financas_service.registrar_gasto_pessoal,
            ao_listar=lambda: self._financas_service.listar_gastos_pessoais(self._usuario.id),
            ao_excluir=self._excluir_lancamento,
            usuario_id=self._usuario.id,
            placeholder_descricao="Ex: Almoço, aluguel, internet...",
        )
        self._painel_pessoal.pack(fill="both", expand=True)

        self._painel_manutencao = _PainelCategoriaGasto(
            aba_manutencao,
            ao_registrar=self._financas_service.registrar_gasto_manutencao,
            ao_listar=lambda: self._financas_service.listar_gastos_manutencao(self._usuario.id),
            ao_excluir=self._excluir_lancamento,
            usuario_id=self._usuario.id,
            placeholder_descricao="Ex: Troca de óleo, pneu, revisão...",
        )
        self._painel_manutencao.pack(fill="both", expand=True)

    def _excluir_lancamento(self, lancamento: Lancamento) -> None:
        self._financas_service.excluir_lancamento(lancamento.id, self._usuario.id)
        self._painel_pessoal.recarregar()
        self._painel_manutencao.recarregar()


class _PainelCategoriaGasto(ctk.CTkFrame):
    """
    Painel reutilizado dentro de cada aba (Pessoal/Manutenção): formulário
    de novo gasto no topo e lista rolável dos lançamentos já registrados.

    É uma classe "privada" deste módulo (prefixo _) porque não faz
    sentido ser reutilizada fora do contexto da GastosView.
    """

    def __init__(
        self,
        master,
        ao_registrar: Callable[[int, str, str], Lancamento],
        ao_listar: Callable[[], List[Lancamento]],
        ao_excluir: Callable[[Lancamento], None],
        usuario_id: int,
        placeholder_descricao: str,
    ):
        super().__init__(master, fg_color="transparent")

        self._ao_registrar = ao_registrar
        self._ao_listar = ao_listar
        self._ao_excluir = ao_excluir
        self._usuario_id = usuario_id

        self._construir_formulario(placeholder_descricao)
        self._construir_lista()
        self.recarregar()

    def _construir_formulario(self, placeholder_descricao: str) -> None:
        linha_campos = ctk.CTkFrame(self, fg_color="transparent")
        linha_campos.pack(fill="x", pady=(styles.ESPACO_MEDIO, 0), padx=styles.ESPACO_MEDIO)
        linha_campos.grid_columnconfigure(0, weight=2)
        linha_campos.grid_columnconfigure(1, weight=1)

        self._campo_descricao = CampoTexto(linha_campos, rotulo="Descrição", placeholder=placeholder_descricao)
        self._campo_descricao.grid(row=0, column=0, sticky="ew", padx=(0, styles.ESPACO_PEQUENO))

        self._campo_valor = CampoTexto(linha_campos, rotulo="Valor", placeholder="Ex: 45,00")
        self._campo_valor.grid(row=0, column=1, sticky="ew")

        self._mensagem_status = criar_mensagem_status(self)
        self._mensagem_status.pack(fill="x", padx=styles.ESPACO_MEDIO, pady=(6, 0))

        botao_adicionar = criar_botao_primario(self, "Adicionar gasto", self._tratar_adicionar)
        botao_adicionar.pack(fill="x", padx=styles.ESPACO_MEDIO, pady=(styles.ESPACO_PEQUENO, styles.ESPACO_MEDIO))

    def _construir_lista(self) -> None:
        self._area_lista = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=colors.LARANJA_VIBRANTE,
            scrollbar_button_hover_color=colors.LARANJA_HOVER,
        )
        self._area_lista.pack(fill="both", expand=True, padx=styles.ESPACO_MEDIO, pady=(0, styles.ESPACO_MEDIO))

    def _tratar_adicionar(self) -> None:
        self._mensagem_status.configure(text="")

        try:
            self._ao_registrar(
                self._usuario_id, self._campo_descricao.get(), self._campo_valor.get()
            )
            self._campo_descricao.entry.delete(0, "end")
            self._campo_valor.entry.delete(0, "end")
            self.recarregar()
        except LancamentoException as erro:
            self._mensagem_status.configure(text=str(erro))
        except Exception:
            self._mensagem_status.configure(text="Não foi possível adicionar o gasto agora.")

    def recarregar(self) -> None:
        """Limpa e reconstrói a lista de lançamentos exibida na aba."""
        for widget_filho in self._area_lista.winfo_children():
            widget_filho.destroy()

        lancamentos = self._ao_listar()

        if not lancamentos:
            ctk.CTkLabel(
                self._area_lista, text="Nenhum gasto registrado ainda.",
                font=styles.FONTE_TEXTO, text_color=colors.TEXTO_SECUNDARIO,
            ).pack(pady=styles.ESPACO_GRANDE)
            return

        for lancamento in lancamentos:
            linha = LinhaLancamento(self._area_lista, lancamento, ao_excluir=self._tratar_excluir)
            linha.pack(fill="x", pady=4)

    def _tratar_excluir(self, lancamento: Lancamento) -> None:
        self._ao_excluir(lancamento)
