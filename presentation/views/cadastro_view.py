"""
Tela de Cadastro.

Além de capturar os dados e delegar ao AuthService (mesmo padrão da
LoginView), esta tela tem uma responsabilidade extra: popular os
campos de Estado e Cidade dinamicamente a partir da API do IBGE.

Como chamadas de rede podem demorar, elas SEMPRE rodam em uma thread
separada (`threading.Thread`) — nunca na thread principal do Tkinter,
para a janela não "congelar" enquanto espera a resposta da internet.
A atualização dos widgets, porém, sempre volta para a thread principal
através de `self.after(0, ...)`, pois o Tkinter não é thread-safe.
"""

import threading
from typing import Callable, Dict, List

import customtkinter as ctk

from config.settings import APLICATIVOS_PADRAO
from domain.entities.usuario import Usuario
from domain.exceptions.auth_exceptions import AuthException
from domain.services.auth_service import AuthService
from domain.services.ibge_service import (
    IBGEServiceException,
    buscar_cidades_por_estado,
    buscar_estados,
)
from domain.validators.senha_validator import calcular_nivel_forca
from presentation.components.telefone_mask import aplicar_mascara_telefone
from presentation.components.widgets import (
    CampoTexto,
    ComboboxCampo,
    criar_botao_link,
    criar_botao_primario,
    criar_mensagem_status,
    criar_subtitulo,
    criar_titulo,
)
from presentation.theme import colors, styles

# Cores usadas para dar feedback visual do nível de força da senha
_COR_POR_FORCA = {
    "Fraca": colors.VERMELHO_SALDO_NEGATIVO,
    "Média": colors.LARANJA_VIBRANTE,
    "Forte": colors.VERDE_SALDO_POSITIVO,
}


class CadastroView(ctk.CTkFrame):
    """Frame de Cadastro de um novo motoboy no sistema."""

    def __init__(
        self,
        master,
        ao_cadastrar_com_sucesso: Callable[[Usuario], None],
        ao_ir_para_login: Callable[[], None],
    ):
        super().__init__(master, fg_color=colors.FUNDO_PRINCIPAL)

        self._auth_service = AuthService()
        self._ao_cadastrar_com_sucesso = ao_cadastrar_com_sucesso
        self._ao_ir_para_login = ao_ir_para_login

        # Mapeia o texto exibido no combobox (ex: "SP - São Paulo") para
        # a sigla real (ex: "SP"), que é o que a API do IBGE espera.
        self._mapa_estados: Dict[str, str] = {}
        self._variaveis_aplicativos: Dict[str, ctk.BooleanVar] = {}

        self._construir_interface()
        self._carregar_estados_em_segundo_plano()

    # ------------------------------------------------------------------
    # Construção da interface
    # ------------------------------------------------------------------

    def _construir_interface(self) -> None:
        area_rolavel = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=colors.LARANJA_VIBRANTE,
            scrollbar_button_hover_color=colors.LARANJA_HOVER,
        )
        area_rolavel.pack(fill="both", expand=True, padx=styles.ESPACO_GRANDE, pady=styles.ESPACO_GRANDE)

        container = ctk.CTkFrame(area_rolavel, fg_color="transparent")
        container.pack(fill="x", expand=True)

        criar_titulo(container, "Criar minha conta").pack(anchor="w")
        criar_subtitulo(container, "Preencha seus dados para começar a correr.").pack(
            anchor="w", pady=(0, styles.ESPACO_GRANDE)
        )

        self._campo_nome = CampoTexto(container, rotulo="Nome completo", placeholder="Seu nome completo")
        self._campo_nome.pack(fill="x", pady=(0, styles.ESPACO_MEDIO))

        self._campo_telefone = CampoTexto(container, rotulo="Telefone", placeholder="16 99123-4567")
        self._campo_telefone.pack(fill="x", pady=(0, styles.ESPACO_MEDIO))
        aplicar_mascara_telefone(self._campo_telefone.entry)

        linha_localizacao = ctk.CTkFrame(container, fg_color="transparent")
        linha_localizacao.pack(fill="x", pady=(0, styles.ESPACO_MEDIO))
        linha_localizacao.grid_columnconfigure(0, weight=1)
        linha_localizacao.grid_columnconfigure(1, weight=2)

        self._campo_estado = ComboboxCampo(linha_localizacao, rotulo="Estado", valores=["Carregando..."])
        self._campo_estado.grid(row=0, column=0, sticky="ew", padx=(0, styles.ESPACO_PEQUENO))
        self._campo_estado.combobox.configure(command=self._ao_selecionar_estado)

        self._campo_cidade = ComboboxCampo(linha_localizacao, rotulo="Cidade", valores=["Selecione o estado"])
        self._campo_cidade.grid(row=0, column=1, sticky="ew")

        self._construir_selecao_aplicativos(container)

        self._campo_senha = CampoTexto(
            container, rotulo="Senha", placeholder="Mínimo 6 caracteres", mostrar_como_senha=True
        )
        self._campo_senha.pack(fill="x", pady=(styles.ESPACO_MEDIO, 2))
        self._campo_senha.entry.bind("<KeyRelease>", self._atualizar_forca_senha)

        self._label_forca_senha = ctk.CTkLabel(
            container, text="", font=styles.FONTE_ERRO, anchor="w",
        )
        self._label_forca_senha.pack(fill="x", pady=(0, styles.ESPACO_MEDIO))

        self._campo_confirmar_senha = CampoTexto(
            container, rotulo="Confirmar senha", placeholder="Repita a senha", mostrar_como_senha=True
        )
        self._campo_confirmar_senha.pack(fill="x")

        self._mensagem_status = criar_mensagem_status(container)
        self._mensagem_status.pack(fill="x", pady=(styles.ESPACO_MEDIO, 0))

        botao_cadastrar = criar_botao_primario(container, "Criar conta", self._tratar_cadastro)
        botao_cadastrar.pack(fill="x", pady=(styles.ESPACO_MEDIO, styles.ESPACO_PEQUENO))

        botao_login = criar_botao_link(container, "Já tenho conta, entrar", self._ao_ir_para_login)
        botao_login.pack()

    def _construir_selecao_aplicativos(self, master) -> None:
        """
        Monta a grade de checkboxes dos aplicativos de entrega.

        Usamos uma grade de 2 colunas (em vez de uma lista vertical)
        para não deixar o formulário excessivamente longo, já que a
        tela inteira já é rolável.
        """
        label_aplicativos = ctk.CTkLabel(
            master, text="Aplicativos que você utiliza", font=styles.FONTE_LABEL,
            text_color=colors.TEXTO_SECUNDARIO, anchor="w",
        )
        label_aplicativos.pack(fill="x", pady=(0, styles.ESPACO_PEQUENO))

        grade_apps = ctk.CTkFrame(master, fg_color="transparent")
        grade_apps.pack(fill="x", pady=(0, styles.ESPACO_MEDIO))
        grade_apps.grid_columnconfigure((0, 1), weight=1)

        for indice, nome_app in enumerate(APLICATIVOS_PADRAO):
            variavel = ctk.BooleanVar(value=False)
            self._variaveis_aplicativos[nome_app] = variavel

            checkbox = ctk.CTkCheckBox(
                grade_apps,
                text=nome_app,
                variable=variavel,
                font=styles.FONTE_TEXTO,
                text_color=colors.TEXTO_PRINCIPAL,
                fg_color=colors.LARANJA_VIBRANTE,
                hover_color=colors.LARANJA_HOVER,
                border_color=colors.BORDA,
                checkmark_color=colors.FUNDO_PRINCIPAL,
            )
            linha, coluna = divmod(indice, 2)
            checkbox.grid(row=linha, column=coluna, sticky="w", pady=4, padx=(0, 8))

    # ------------------------------------------------------------------
    # Integração com a API do IBGE (roda fora da thread principal)
    # ------------------------------------------------------------------

    def _carregar_estados_em_segundo_plano(self) -> None:
        self._campo_estado.combobox.configure(state="disabled")
        thread = threading.Thread(target=self._buscar_estados_na_thread, daemon=True)
        thread.start()

    def _buscar_estados_na_thread(self) -> None:
        """Executa em background. NUNCA mexe em widgets diretamente aqui."""
        try:
            estados = buscar_estados()
            self.after(0, lambda: self._popular_combobox_estados(estados))
        except IBGEServiceException as erro:
            self.after(0, lambda: self._exibir_erro_geral(str(erro)))

    def _popular_combobox_estados(self, estados: List[dict]) -> None:
        self._mapa_estados = {
            f"{estado['sigla']} - {estado['nome']}": estado["sigla"] for estado in estados
        }
        opcoes = list(self._mapa_estados.keys())

        # IMPORTANTE: o CTkComboBox só sabe escrever um valor via `.set()`
        # quando está em estado "readonly" ou "normal" — em estado
        # "disabled" (como deixamos durante o carregamento) o `.set()`
        # simplesmente não tem efeito nenhum. Por isso reabilitamos
        # ANTES de popular os valores, nunca depois.
        self._campo_estado.combobox.configure(state="readonly")
        self._campo_estado.definir_valores(opcoes)

        if opcoes:
            self._ao_selecionar_estado(opcoes[0])

    def _ao_selecionar_estado(self, valor_selecionado: str) -> None:
        """
        Disparado quando o usuário escolhe um estado no combobox.
        Busca as cidades correspondentes em uma nova thread.
        """
        sigla_uf = self._mapa_estados.get(valor_selecionado)
        if not sigla_uf:
            return

        self._campo_cidade.definir_valores(["Carregando..."])
        self._campo_cidade.combobox.configure(state="disabled")

        thread = threading.Thread(
            target=self._buscar_cidades_na_thread, args=(sigla_uf,), daemon=True
        )
        thread.start()

    def _buscar_cidades_na_thread(self, sigla_uf: str) -> None:
        try:
            cidades = buscar_cidades_por_estado(sigla_uf)
            self.after(0, lambda: self._popular_combobox_cidades(cidades))
        except IBGEServiceException as erro:
            self.after(0, lambda: self._exibir_erro_geral(str(erro)))

    def _popular_combobox_cidades(self, cidades: List[str]) -> None:
        # Mesma ordem corrigida do combobox de estados: primeiro reabilita,
        # depois define os valores (ver comentário em _popular_combobox_estados).
        self._campo_cidade.combobox.configure(state="readonly")
        self._campo_cidade.definir_valores(cidades)

    # ------------------------------------------------------------------
    # Feedback visual de força da senha
    # ------------------------------------------------------------------

    def _atualizar_forca_senha(self, _evento=None) -> None:
        senha_digitada = self._campo_senha.entry.get()

        if not senha_digitada:
            self._label_forca_senha.configure(text="")
            return

        nivel = calcular_nivel_forca(senha_digitada)
        cor = _COR_POR_FORCA.get(nivel, colors.TEXTO_SECUNDARIO)
        self._label_forca_senha.configure(text=f"Força da senha: {nivel}", text_color=cor)

    # ------------------------------------------------------------------
    # Submissão do formulário
    # ------------------------------------------------------------------

    def _tratar_cadastro(self) -> None:
        self._limpar_mensagens()

        aplicativos_marcados = [
            nome for nome, variavel in self._variaveis_aplicativos.items() if variavel.get()
        ]

        try:
            usuario = self._auth_service.cadastrar_usuario(
                nome_completo=self._campo_nome.get(),
                telefone=self._campo_telefone.get(),
                cidade=self._campo_cidade.get(),
                estado_uf=self._mapa_estados.get(self._obter_estado_selecionado(), ""),
                senha=self._campo_senha.entry.get(),
                confirmar_senha=self._campo_confirmar_senha.entry.get(),
                aplicativos=aplicativos_marcados,
            )
            self._ao_cadastrar_com_sucesso(usuario)
        except AuthException as erro:
            self._exibir_erro_geral(str(erro))
        except Exception:
            self._exibir_erro_geral(
                "Não foi possível concluir o cadastro agora. Tente novamente em instantes."
            )

    def _obter_estado_selecionado(self) -> str:
        """
        Retorna o texto bruto selecionado no combobox de estado
        (ex: "SP - São Paulo"), usado depois como chave em
        `self._mapa_estados` para extrair só a sigla.
        """
        return self._campo_estado.combobox.get()

    def _exibir_erro_geral(self, mensagem: str) -> None:
        self._mensagem_status.configure(text=mensagem)

    def _limpar_mensagens(self) -> None:
        self._mensagem_status.configure(text="")
        for campo in (self._campo_nome, self._campo_telefone, self._campo_cidade, self._campo_estado):
            campo.limpar_erro()
