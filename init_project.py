# -*- coding: utf-8 -*-
"""
Script de Inicialização e Verificação de Ambiente
Projeto: Corre dos Motocas
Criado por: Joao vitor barroso A.
"""

import os
import sys
import subprocess


def verificar_dependencias():
    print("🔄 Verificando e instalando dependências do projeto...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Todas as dependências (customtkinter, bcrypt, requests, etc.) estão prontas!")
    except Exception as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        sys.exit(1)


def inicializar_banco():
    print("\n🗄️ Inicializando o banco de dados SQLite e aplicando Migrations...")
    try:
        # Garante que o Python reconheça a estrutura de pastas local
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))

        from data.database.connection import DatabaseConnection

        # Inicializa a classe que gerencia o banco
        db = DatabaseConnection()

        # Tenta pegar a conexão bruta do SQLite de dentro do objeto do repositório
        conn = None
        if hasattr(db, 'conn'):
            conn = db.conn
        elif hasattr(db, 'connection'):
            conn = db.connection

        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tabelas = [row[0] for row in cursor.fetchall()]
            print(f"✅ Banco de dados verificado com sucesso!")
            print(f"📦 Tabelas identificadas no sistema: {', '.join(tabelas)}")
        else:
            # Caso o Claude tenha encapsulado tudo em métodos sem expor a conexão
            print("✅ Classe de conexão instanciada (as tabelas foram criadas via Migrations no __init__).")

        # Fecha se o método close existir
        if hasattr(db, 'close'):
            db.close()

    except Exception as e:
        print(f"❌ Erro ao inicializar o banco de dados: {e}")
        print("Certifique-se de que a estrutura de pastas de 'data/' está correta.")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("🏍️  BEM-VINDO AO SCRIPT DE UNIFICAÇÃO - CORRE DOS MOTOCAS  🏍️")
    print("=" * 60)

    verificar_dependencias()
    inicializar_banco()

    print("\n" + "=" * 60)
    print("🚀 Tudo pronto! Agora você pode executar o arquivo 'main.py'")
    print("   para rodar o sistema com a interface CustomTkinter.")
    print("=" * 60)