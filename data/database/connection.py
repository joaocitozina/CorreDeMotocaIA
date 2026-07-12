"""
Camada de conexão com o banco de dados SQLite.

Este módulo é responsável exclusivamente por:
    1. Abrir/gerenciar a conexão com o arquivo .db
    2. Criar as tabelas do sistema (migrations simples e idempotentes)

Nenhuma regra de negócio deve entrar aqui — isso é responsabilidade do
Domain. Aqui só existe "como falar com o SQLite".
"""

import sqlite3
from contextlib import contextmanager

from config.settings import APLICATIVOS_PADRAO, DATABASE_PATH


class DatabaseConnection:
    """
    Responsável por abrir conexões com o SQLite e garantir que o schema
    (estrutura de tabelas) exista antes do app ser usado.

    Usamos o padrão de "gerenciador de contexto" (with ... as) para que
    cada conexão seja sempre fechada corretamente, mesmo se ocorrer erro
    no meio de uma operação — isso evita banco de dados travado/corrompido.
    """

    def __init__(self, database_path: str = DATABASE_PATH):
        self.database_path = database_path

    @contextmanager
    def get_connection(self):
        """
        Abre uma conexão com o banco e garante o fechamento automático.

        PRAGMA foreign_keys=ON é ativado porque o SQLite, por padrão,
        NÃO valida chaves estrangeiras — precisamos ligar isso manualmente
        em cada conexão para manter a integridade referencial dos dados.
        """
        connection = sqlite3.connect(self.database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        # row_factory permite acessar colunas pelo nome (linha["nome"])
        # em vez de só pelo índice (linha[0]), o que deixa o código
        # muito mais legível nas camadas de repositório.
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            # Se qualquer coisa der errado durante o uso da conexão,
            # desfazemos as alterações para não deixar o banco em
            # estado parcial/inconsistente.
            connection.rollback()
            raise
        finally:
            connection.close()

    def criar_tabelas(self) -> None:
        """
        Cria todas as tabelas do sistema caso ainda não existam.

        Usamos "CREATE TABLE IF NOT EXISTS" para que este método possa
        ser chamado sempre que o app iniciar, sem risco de apagar dados
        já existentes ou lançar erro em execuções subsequentes.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Tabela principal de usuários (motoboys cadastrados no app).
            # A senha NUNCA é salva em texto puro — apenas o hash bcrypt.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_completo TEXT NOT NULL,
                    telefone TEXT NOT NULL UNIQUE,
                    cidade TEXT NOT NULL,
                    estado_uf TEXT NOT NULL,
                    senha_hash TEXT NOT NULL,
                    data_cadastro TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    ativo INTEGER NOT NULL DEFAULT 1
                )
            """)

            # Tabela de apps de entrega que o motoboy utiliza (iFood, Rappi, etc).
            # Fica separada em N:N porque um usuário pode usar vários apps
            # e um app é usado por vários usuários — evita repetir texto
            # e facilita relatórios futuros (ex: "quantos usam iFood?").
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aplicativos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL UNIQUE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuario_aplicativos (
                    usuario_id INTEGER NOT NULL,
                    aplicativo_id INTEGER NOT NULL,
                    PRIMARY KEY (usuario_id, aplicativo_id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
                    FOREIGN KEY (aplicativo_id) REFERENCES aplicativos (id) ON DELETE CASCADE
                )
            """)

            # Populamos os apps mais comuns do mercado de entregas.
            # INSERT OR IGNORE evita erro de duplicidade em reinícios do app.
            cursor.executemany(
                "INSERT OR IGNORE INTO aplicativos (nome) VALUES (?)",
                [(app,) for app in APLICATIVOS_PADRAO],
            )

            # Tabela de lançamentos financeiros do motoboy: tanto ENTRADAS
            # (corridas/ganhos) quanto SAÍDAS (gastos pessoais e de
            # manutenção da moto). O campo `natureza` diferencia entrada
            # de saída, e `categoria` diferencia o tipo de saída — assim
            # o Dashboard consegue somar tudo com queries simples de SQL,
            # sem precisar de tabelas separadas por categoria.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lancamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    natureza TEXT NOT NULL CHECK (natureza IN ('entrada', 'saida')),
                    categoria TEXT NOT NULL CHECK (categoria IN ('corrida', 'pessoal', 'manutencao')),
                    descricao TEXT NOT NULL,
                    valor REAL NOT NULL CHECK (valor > 0),
                    data_registro TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
                )
            """)


# Instância única (singleton simples) compartilhada pela aplicação.
# Evita que cada repositório precise saber o caminho do banco.
db_connection = DatabaseConnection()
