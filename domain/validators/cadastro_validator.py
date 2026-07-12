"""
Validação agregada do formulário de Cadastro de Usuário.

Este módulo orquestra as validações menores (senha, telefone, campos
vazios) em uma única função de alto nível, para que a camada de
Presentation só precise fazer UMA chamada e tratar exceções específicas,
sem espalhar "ifs" de validação dentro da tela.
"""

from typing import List

from domain.exceptions.auth_exceptions import (
    AplicativosNaoSelecionadosException,
    CampoObrigatorioException,
    LocalizacaoInvalidaException,
    SenhasNaoConferemException,
)
from domain.validators.senha_validator import validar_forca_senha
from domain.validators.telefone_validator import validar_telefone


def validar_campos_obrigatorios(nome_completo: str, senha: str, confirmar_senha: str) -> None:
    """
    Garante que os campos de texto livre obrigatórios não estejam vazios.

    Telefone, cidade e estado têm validadores próprios (mais específicos)
    chamados separadamente em validar_formulario_cadastro, então não
    repetimos a checagem de "vazio" para eles aqui.
    """
    campos = {
        "Nome Completo": nome_completo,
        "Senha": senha,
        "Confirmar Senha": confirmar_senha,
    }

    for nome_campo, valor in campos.items():
        if not valor or not valor.strip():
            raise CampoObrigatorioException(nome_campo)


def validar_localizacao(cidade: str, estado_uf: str) -> None:
    """Garante que cidade e estado foram efetivamente selecionados."""
    if not cidade or not cidade.strip() or not estado_uf or not estado_uf.strip():
        raise LocalizacaoInvalidaException()


def validar_aplicativos_selecionados(aplicativos: List[str]) -> None:
    """Garante que ao menos um app de entrega foi marcado pelo usuário."""
    if not aplicativos:
        raise AplicativosNaoSelecionadosException()


def validar_formulario_cadastro(
    nome_completo: str,
    telefone: str,
    cidade: str,
    estado_uf: str,
    senha: str,
    confirmar_senha: str,
    aplicativos: List[str],
) -> str:
    """
    Executa todas as validações do cadastro, na ordem que faz mais
    sentido para o usuário entender o próprio erro primeiro
    (campos vazios > localização > apps > telefone > senha).

    Retorna o telefone já formatado no padrão "XX 9XXXX-XXXX", pronto
    para ser salvo no banco — assim quem chama essa função não precisa
    lidar com formatação separadamente.
    """
    validar_campos_obrigatorios(nome_completo, senha, confirmar_senha)
    validar_localizacao(cidade, estado_uf)
    validar_aplicativos_selecionados(aplicativos)

    telefone_formatado = validar_telefone(telefone)

    if senha != confirmar_senha:
        raise SenhasNaoConferemException()

    validar_forca_senha(senha)

    return telefone_formatado
