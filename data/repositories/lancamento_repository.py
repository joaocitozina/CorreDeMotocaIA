"""
Repositório de Lançamentos financeiros.

Além do CRUD básico, este repositório também expõe consultas agregadas
(totais e somas por categoria) — colocamos essas somas aqui, feitas
diretamente em SQL, porque o banco faz isso de forma muito mais
eficiente do que buscar todas as linhas e somar em Python.
"""

from datetime import datetime
from typing import List, Optional

from data.database.connection import DatabaseConnection, db_connection
from domain.entities.lancamento import Categoria, Lancamento, Natureza


class LancamentoRepository:
    """Encapsula todo o acesso à tabela `lancamentos`."""

    def __init__(self, connection: DatabaseConnection = db_connection):
        self._connection = connection

    def salvar(self, lancamento: Lancamento) -> Lancamento:
        """Insere um novo lançamento e devolve o objeto com o `id` preenchido."""
        with self._connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO lancamentos (usuario_id, natureza, categoria, descricao, valor)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    lancamento.usuario_id,
                    lancamento.natureza.value,
                    lancamento.categoria.value,
                    lancamento.descricao,
                    lancamento.valor,
                ),
            )
            lancamento.id = cursor.lastrowid
        return lancamento

    def excluir(self, lancamento_id: int, usuario_id: int) -> None:
        """
        Remove um lançamento pelo id.

        Exigimos também o `usuario_id` na cláusula WHERE como uma
        segunda camada de proteção: mesmo que um id de outro usuário
        vaze para a tela por engano, a exclusão nunca vai afetar dados
        de quem não é o dono do lançamento.
        """
        with self._connection.get_connection() as conn:
            conn.execute(
                "DELETE FROM lancamentos WHERE id = ? AND usuario_id = ?",
                (lancamento_id, usuario_id),
            )

    def listar_por_usuario(
        self, usuario_id: int, categoria: Optional[Categoria] = None
    ) -> List[Lancamento]:
        """
        Lista os lançamentos de um usuário, do mais recente para o mais
        antigo. Se `categoria` for informada, filtra só por ela — usado
        pelas abas "Pessoais" e "Manutenção" da tela de Gastos.
        """
        with self._connection.get_connection() as conn:
            cursor = conn.cursor()

            if categoria is not None:
                cursor.execute(
                    """
                    SELECT * FROM lancamentos
                    WHERE usuario_id = ? AND categoria = ?
                    ORDER BY data_registro DESC, id DESC
                    """,
                    (usuario_id, categoria.value),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM lancamentos
                    WHERE usuario_id = ?
                    ORDER BY data_registro DESC, id DESC
                    """,
                    (usuario_id,),
                )

            return [self._montar_lancamento(linha) for linha in cursor.fetchall()]

    def calcular_totais(self, usuario_id: int) -> dict:
        """
        Retorna um resumo financeiro agregado do usuário:
        total ganho, total gasto (pessoal + manutenção) e saldo.

        Centralizar essa conta em SQL (SUM/CASE) evita trazer milhares
        de linhas para a memória só para somar — importante conforme o
        histórico de lançamentos do motoboy cresce.
        """
        with self._connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN natureza = 'entrada' THEN valor ELSE 0 END), 0) AS total_ganhos,
                    COALESCE(SUM(CASE WHEN categoria = 'pessoal' THEN valor ELSE 0 END), 0) AS total_pessoal,
                    COALESCE(SUM(CASE WHEN categoria = 'manutencao' THEN valor ELSE 0 END), 0) AS total_manutencao
                FROM lancamentos
                WHERE usuario_id = ?
                """,
                (usuario_id,),
            )
            linha = cursor.fetchone()

        total_ganhos = linha["total_ganhos"]
        total_pessoal = linha["total_pessoal"]
        total_manutencao = linha["total_manutencao"]
        total_gastos = total_pessoal + total_manutencao

        return {
            "total_ganhos": total_ganhos,
            "total_pessoal": total_pessoal,
            "total_manutencao": total_manutencao,
            "total_gastos": total_gastos,
            "saldo": total_ganhos - total_gastos,
        }

    def _montar_lancamento(self, linha) -> Lancamento:
        """Converte uma linha do SQLite em um objeto Lancamento do domínio."""
        data_registro = None
        if linha["data_registro"]:
            data_registro = datetime.strptime(linha["data_registro"], "%Y-%m-%d %H:%M:%S")

        return Lancamento(
            id=linha["id"],
            usuario_id=linha["usuario_id"],
            natureza=Natureza(linha["natureza"]),
            categoria=Categoria(linha["categoria"]),
            descricao=linha["descricao"],
            valor=linha["valor"],
            data_registro=data_registro,
        )
