"""
Serviço (UseCase) de Autenticação.

Este é o "maestro" da área de login/cadastro: orquestra validações do
Domain, hashing de senha com bcrypt e persistência via Repository,
sem se preocupar com COMO os dados chegam até aqui (isso é problema
da tela) nem com COMO são armazenados fisicamente (isso é problema
do repositório). Ele só conhece regras de negócio.
"""

from typing import List

import bcrypt

from config.settings import BCRYPT_ROUNDS
from data.repositories.usuario_repository import UsuarioRepository
from domain.entities.usuario import Usuario
from domain.exceptions.auth_exceptions import (
    CredenciaisInvalidasException,
    UsuarioJaExisteException,
)
from domain.validators.cadastro_validator import validar_formulario_cadastro
from domain.validators.telefone_validator import limpar_telefone, validar_telefone


class AuthService:
    """
    Caso de uso de Autenticação: cadastrar novo usuário e autenticar
    login. Depende apenas de abstrações simples (o repositório), o que
    facilita testes automatizados (podemos injetar um repositório falso).
    """

    def __init__(self, usuario_repository: UsuarioRepository = None):
        self._usuario_repository = usuario_repository or UsuarioRepository()

    def cadastrar_usuario(
        self,
        nome_completo: str,
        telefone: str,
        cidade: str,
        estado_uf: str,
        senha: str,
        confirmar_senha: str,
        aplicativos: List[str],
    ) -> Usuario:
        """
        Executa o fluxo completo de cadastro de um novo motoboy:

            1. Valida todos os campos do formulário (Domain)
            2. Garante que o telefone ainda não está cadastrado
            3. Gera o hash bcrypt da senha (nunca salva em texto puro)
            4. Persiste o usuário através do Repository (Data)

        Retorna o Usuario já persistido, com o `id` preenchido.
        """
        telefone_formatado = validar_formulario_cadastro(
            nome_completo=nome_completo,
            telefone=telefone,
            cidade=cidade,
            estado_uf=estado_uf,
            senha=senha,
            confirmar_senha=confirmar_senha,
            aplicativos=aplicativos,
        )

        usuario_existente = self._usuario_repository.buscar_por_telefone(telefone_formatado)
        if usuario_existente is not None:
            raise UsuarioJaExisteException(telefone_formatado)

        senha_hash = self._gerar_hash_senha(senha)

        novo_usuario = Usuario(
            nome_completo=nome_completo.strip(),
            telefone=telefone_formatado,
            cidade=cidade.strip(),
            estado_uf=estado_uf.strip().upper(),
            senha_hash=senha_hash,
            aplicativos=aplicativos,
        )

        return self._usuario_repository.salvar(novo_usuario)

    def autenticar(self, telefone: str, senha: str) -> Usuario:
        """
        Executa o fluxo de login: localiza o usuário pelo telefone e
        confere a senha informada contra o hash salvo no banco.

        Propositalmente usamos a MESMA mensagem de erro tanto para
        "telefone não encontrado" quanto para "senha errada"
        (CredenciaisInvalidasException), por segurança — não damos
        pistas de qual dos dois dados está incorreto.
        """
        if not telefone or not telefone.strip():
            raise CredenciaisInvalidasException()

        if not senha:
            raise CredenciaisInvalidasException()

        try:
            telefone_formatado = validar_telefone(telefone)
        except Exception:
            # Se o telefone nem sequer tem um formato válido, já sabemos
            # que a credencial está incorreta — não faz sentido nem
            # consultar o banco.
            raise CredenciaisInvalidasException()

        usuario = self._usuario_repository.buscar_por_telefone(telefone_formatado)

        if usuario is None or not usuario.ativo:
            raise CredenciaisInvalidasException()

        if not self._conferir_senha(senha, usuario.senha_hash):
            raise CredenciaisInvalidasException()

        return usuario

    def _gerar_hash_senha(self, senha: str) -> str:
        """
        Gera o hash bcrypt da senha.

        O bcrypt já embute um "salt" aleatório automaticamente em cada
        hash gerado, então duas senhas iguais produzem hashes diferentes
        — isso é o que garante conformidade com a LGPD ao proteger a
        senha mesmo em caso de vazamento do banco de dados.
        """
        senha_bytes = senha.encode("utf-8")
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        hash_gerado = bcrypt.hashpw(senha_bytes, salt)
        # Convertido para string pois o SQLite armazena texto (coluna TEXT),
        # e bcrypt.hashpw devolve bytes.
        return hash_gerado.decode("utf-8")

    def _conferir_senha(self, senha_digitada: str, senha_hash_salva: str) -> bool:
        """
        Confere se a senha digitada no login corresponde ao hash salvo.

        bcrypt.checkpw() extrai o salt automaticamente do próprio hash
        salvo, recalcula e compara de forma segura (resistente a
        "timing attacks"), então nunca comparamos hashes com `==` direto.
        """
        return bcrypt.checkpw(
            senha_digitada.encode("utf-8"),
            senha_hash_salva.encode("utf-8"),
        )
