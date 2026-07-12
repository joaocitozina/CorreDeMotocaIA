"""
Configurações globais do projeto "Corre dos Motocas".

Centralizamos aqui caminhos e constantes que são usados em mais de uma
camada da aplicação. Isso evita "strings mágicas" espalhadas pelo código
e facilita a manutenção caso, no futuro, o banco mude de lugar ou o nome
do app mude.
"""

import os

# Diretório raiz do projeto (a pasta onde este arquivo está, subindo um nível)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Pasta onde os dados persistentes ficam salvos (banco SQLite, logs, etc.)
DATA_DIR = os.path.join(BASE_DIR, "storage")

# Caminho final do arquivo do banco de dados SQLite
DATABASE_PATH = os.path.join(DATA_DIR, "corre_dos_motocas.db")

# Nome exibido em janelas, logs e mensagens de erro
APP_NAME = "Corre dos Motocas"

# Custo do algoritmo bcrypt (quanto maior, mais seguro e mais lento).
# 12 é o padrão recomendado atualmente como bom equilíbrio custo/benefício.
BCRYPT_ROUNDS = 12

# Timeout (em segundos) para chamadas à API pública do IBGE
IBGE_API_TIMEOUT = 8

# Lista padrão de aplicativos de entrega oferecidos no cadastro.
# Centralizada aqui para ser a ÚNICA fonte da verdade: tanto a migration
# do banco (data/database/connection.py) quanto a tela de Cadastro
# (presentation/views/cadastro_view.py) consultam esta mesma lista,
# evitando que fiquem dessincronizadas no futuro.
APLICATIVOS_PADRAO = [
    "iFood", "Rappi", "Uber Eats", "99Food",
    "Loggi", "Zé Delivery", "Particular",
]

# --- Integração com clima (aba "Dicas do Dia") ---------------------------
# Chave gratuita da OpenWeatherMap (https://openweathermap.org/api).
# Buscamos primeiro na variável de ambiente (forma recomendada de manter
# a chave fora do código-fonte) e caímos para string vazia como padrão.
# Com a chave vazia, o serviço de clima informa educadamente que a
# integração ainda não foi configurada, em vez de quebrar o app.
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
OPENWEATHER_API_TIMEOUT = 8

# --- Integração com IA (geração de dicas do dia) --------------------------
# Chave da API do Google Gemini (google-generativeai). Também opcional:
# sem chave configurada, o app usa o MODO SIMULADO — um motor de regras
# local que gera dicas coerentes com o clima e as normas do Detran-SP,
# sem custo nenhum e sem depender de internet para essa parte específica.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
USAR_IA_SIMULADA = GEMINI_API_KEY == ""

# Garante que a pasta de dados exista antes de qualquer tentativa de conexão
os.makedirs(DATA_DIR, exist_ok=True)
