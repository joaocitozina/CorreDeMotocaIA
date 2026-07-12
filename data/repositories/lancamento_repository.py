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
                INSERT INTO lancamentos (usuario_id, natureza, categoria, descricao, valor, aplicativo)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    lancamento.usuario_id,
                    lancamento.natureza.value,
                    lancamento.categoria.value,
                    lancamento.descricao,
                    lancamento.valor,
                    lancamento.aplicativo,
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

    def obter_ganhos_por_app(self, usuario_id: int, periodo: Optional[str] = None) -> dict:
        """
        Agrupa e soma os ganhos (natureza='entrada', categoria='corrida')
        por aplicativo de entrega — é a informação usada pela tela de
        Ganhos Detalhados para montar tanto o gráfico de barras quanto
        a listagem por app.

        Fazemos o agrupamento com SUM/GROUP BY diretamente em SQL (em
        vez de trazer todos os lançamentos e somar em Python) porque o
        banco faz isso de forma muito mais eficiente, e porque é
        exatamente para isso que o SQL existe.

        `periodo` é opcional e aceita "diario", "semanal" ou "mensal"
        (usado pelas abas da tela de Ganhos). Quando None, soma o
        histórico completo do usuário, sem filtro de data.

        Lançamentos sem aplicativo definido (registrados antes desta
        correção, ou o atalho rápido do Dashboard) entram agrupados
        como "Outros" via COALESCE, para nenhum valor ficar de fora do
        relatório.
        """
        filtro_periodo_sql, parametros_periodo = self._montar_filtro_periodo(periodo)

        with self._connection.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                    COALESCE(aplicativo, 'Outros') AS nome_app,
                    SUM(valor) AS total
                FROM lancamentos
                WHERE usuario_id = ? AND natureza = 'entrada' AND categoria = 'corrida'
                {filtro_periodo_sql}
                GROUP BY COALESCE(aplicativo, 'Outros')
                ORDER BY total DESC
                """,
                (usuario_id, *parametros_periodo),
            )
            linhas = cursor.fetchall()

        return {linha["nome_app"]: round(linha["total"], 2) for linha in linhas}

    @staticmethod
    def _montar_filtro_periodo(periodo: Optional[str]) -> tuple:
        """
        Monta o trecho SQL (e os parâmetros correspondentes) que
        restringe a busca a um período de tempo, usando as funções de
        data nativas do SQLite — assim a comparação de datas fica a
        cargo do banco, sem precisar trazer tudo para o Python filtrar.

        Retorna uma tupla (trecho_sql, parametros), onde trecho_sql já
        vem pronto para ser concatenado após o WHERE existente (começa
        com "AND ..."), e parametros é a lista de valores para o
        placeholder "?" usado nesse trecho.
        """
        if periodo is None:
            return "", ()

        if periodo == "diario":
            return "AND date(data_registro) = date('now', 'localtime')", ()

        if periodo == "semanal":
            return "AND date(data_registro) >= date('now', 'localtime', '-7 days')", ()

        if periodo == "mensal":
            return (
                "AND strftime('%Y-%m', data_registro) = strftime('%Y-%m', 'now', 'localtime')",
                (),
            )

        raise ValueError(f"Período inválido: {periodo!r}. Use 'diario', 'semanal', 'mensal' ou None.")

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
            aplicativo=linha["aplicativo"],
            data_registro=data_registro,
        )
