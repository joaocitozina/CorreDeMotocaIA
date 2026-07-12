"""
Repositório de Usuários.

Responsável por toda a persistência da entidade Usuario no SQLite:
inserir, buscar por telefone, buscar por id e vincular os aplicativos
de entrega escolhidos no cadastro. Esta camada NÃO valida regras de
negócio (isso é papel do Domain) — ela só sabe "ler e escrever no banco".
"""

from typing import List, Optional

from data.database.connection import DatabaseConnection, db_connection
from domain.entities.usuario import Usuario


class UsuarioRepository:
    """
    Encapsula todo o acesso à tabela `usuarios` (e sua relação N:N com
    `aplicativos`), traduzindo linhas do SQLite em objetos Usuario e
    vice-versa.
    """

    def __init__(self, connection: DatabaseConnection = db_connection):
        self._connection = connection

    def salvar(self, usuario: Usuario) -> Usuario:
        """
        Insere um novo usuário no banco e retorna o objeto atualizado
        com o `id` gerado pelo SQLite (AUTOINCREMENT).

        A operação de salvar o usuário e vincular seus aplicativos
        acontece dentro da MESMA conexão/transação: se vincular um
        aplicativo falhar, o usuário inserido também é desfeito
        (rollback automático do context manager), evitando cadastros
        "pela metade" no banco.
        """
        with self._connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO usuarios (nome_completo, telefone, cidade, estado_uf, senha_hash)
                VALUES (?, ?, ?, ?, ?)
                """,
                (usuario.nome_completo, usuario.telefone, usuario.cidade,
                 usuario.estado_uf, usuario.senha_hash),
            )
            usuario.id = cursor.lastrowid

            self._vincular_aplicativos(cursor, usuario.id, usuario.aplicativos)

        return usuario

    def _vincular_aplicativos(self, cursor, usuario_id: int, nomes_aplicativos: List[str]) -> None:
        """
        Associa os aplicativos de entrega escolhidos (ex: iFood, Rappi)
        ao usuário recém-criado, na tabela de ligação `usuario_aplicativos`.

        Método "privado" (prefixo _) porque é um detalhe interno de
        `salvar()` — nenhuma outra parte do sistema deveria chamá-lo
        isoladamente.
        """
        for nome_app in nomes_aplicativos:
            cursor.execute("SELECT id FROM aplicativos WHERE nome = ?", (nome_app,))
            linha = cursor.fetchone()

            # Caso o usuário informe um app que ainda não está na lista
            # padrão, cadastramos ele na hora ao invés de rejeitar o
            # cadastro — mantém o sistema flexível para novos apps do mercado.
            if linha is None:
                cursor.execute("INSERT INTO aplicativos (nome) VALUES (?)", (nome_app,))
                aplicativo_id = cursor.lastrowid
            else:
                aplicativo_id = linha["id"]

            cursor.execute(
                "INSERT OR IGNORE INTO usuario_aplicativos (usuario_id, aplicativo_id) VALUES (?, ?)",
                (usuario_id, aplicativo_id),
            )

    def buscar_por_telefone(self, telefone: str) -> Optional[Usuario]:
        """
        Busca um usuário pelo telefone (usado no login e na checagem
        de duplicidade durante o cadastro). Retorna None se não existir,
        em vez de lançar exceção — a decisão de "isso é um erro" é da
        camada que chama, não do repositório.
        """
        with self._connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE telefone = ?", (telefone,))
            linha = cursor.fetchone()

            if linha is None:
                return None

            return self._montar_usuario(cursor, linha)

    def buscar_por_id(self, usuario_id: int) -> Optional[Usuario]:
        """Busca um usuário pelo id, já com seus aplicativos vinculados."""
        with self._connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
            linha = cursor.fetchone()

            if linha is None:
                return None

            return self._montar_usuario(cursor, linha)

    def _montar_usuario(self, cursor, linha) -> Usuario:
        """
        Converte uma linha da tabela `usuarios` (mais seus aplicativos
        relacionados) em um objeto de domínio Usuario totalmente montado.

        Centralizar essa montagem evita repetir a mesma lógica em
        buscar_por_telefone e buscar_por_id.
        """
        cursor.execute(
            """
            SELECT a.nome FROM aplicativos a
            INNER JOIN usuario_aplicativos ua ON ua.aplicativo_id = a.id
            WHERE ua.usuario_id = ?
            """,
            (linha["id"],),
        )
        aplicativos = [row["nome"] for row in cursor.fetchall()]

        return Usuario(
            id=linha["id"],
            nome_completo=linha["nome_completo"],
            telefone=linha["telefone"],
            cidade=linha["cidade"],
            estado_uf=linha["estado_uf"],
            senha_hash=linha["senha_hash"],
            aplicativos=aplicativos,
            ativo=bool(linha["ativo"]),
        )
