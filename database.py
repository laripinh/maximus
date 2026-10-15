import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "condominio.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de Configurações
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS configuracoes (
        chave TEXT PRIMARY KEY,
        valor TEXT
    )
    """)

    # Tabela de Unidades/Casas (1 a 8)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS casas (
        id INTEGER PRIMARY KEY,
        numero INTEGER UNIQUE,
        identificacao TEXT,
        responsavel TEXT,
        contato TEXT,
        valor_cota REAL DEFAULT 300.00
    )
    """)

    # Tabela de Receitas (Pagamentos de Condomínio)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS receitas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        casa_id INTEGER,
        mes_ano TEXT, -- YYYY-MM
        valor REAL,
        data_pagamento TEXT,
        status TEXT DEFAULT 'PENDENTE', -- PAGO, PENDENTE
        forma_pagamento TEXT DEFAULT 'Pix',
        comprovante_nome TEXT,
        comprovante_path TEXT,
        observacoes TEXT,
        criado_em TEXT,
        FOREIGN KEY (casa_id) REFERENCES casas (id)
    )
    """)

    # Tabela de Despesas (Fixas e Variáveis)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS despesas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT, -- FIXA, VARIAVEL
        categoria TEXT, -- Água, Energia, Funcionário/Limpeza, Manutenção, etc.
        descricao TEXT,
        valor REAL,
        mes_ano TEXT, -- YYYY-MM
        data_vencimento TEXT,
        data_pagamento TEXT,
        status TEXT DEFAULT 'PAGO', -- PAGO, PENDENTE
        comprovante_nome TEXT,
        comprovante_path TEXT,
        observacoes TEXT,
        criado_em TEXT
    )
    """)

    # Inserir configurações padrão se não existirem
    configs_padrao = [
        ("nome_condominio", "Condomínio Residencial Máximus"),
        ("cnpj", "00.000.000/0001-00"),
        ("endereco", "Rua Principal, 100 - Bairro, Cidade - UF"),
        ("dia_vencimento", "10"),
        ("valor_cota_padrao", "300.00"),
        ("saldo_inicial", "0.00")
    ]
    for chave, valor in configs_padrao:
        cursor.execute("INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES (?, ?)", (chave, valor))

    # Inserir as 8 casas padrão caso ainda não existam
    for num in range(1, 9):
        cursor.execute("""
        INSERT OR IGNORE INTO casas (numero, identificacao, responsavel, contato, valor_cota)
        VALUES (?, ?, ?, ?, ?)
        """, (num, f"Casa {num:02d}", f"Morador Casa {num:02d}", "", 300.00))

    conn.commit()
    conn.close()

def get_config(chave, valor_padrao=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracoes WHERE chave = ?", (chave,))
    row = cursor.fetchone()
    conn.close()
    return row["valor"] if row else valor_padrao

def set_config(chave, valor):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)", (chave, str(valor)))
    conn.commit()
    conn.close()

def get_todas_casas():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM casas ORDER BY numero ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_receitas_mes(mes_ano):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT r.*, c.numero, c.identificacao, c.responsavel
    FROM casas c
    LEFT JOIN receitas r ON c.id = r.casa_id AND r.mes_ano = ?
    ORDER BY c.numero ASC
    """, (mes_ano,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def salvar_receita(casa_id, mes_ano, valor, data_pagamento, status, forma_pagamento, comprovante_nome=None, comprovante_path=None, observacoes=""):
    conn = get_connection()
    cursor = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Verifica se já existe registro dessa casa para o mês
    cursor.execute("SELECT id FROM receitas WHERE casa_id = ? AND mes_ano = ?", (casa_id, mes_ano))
    existente = cursor.fetchone()

    if existente:
        if comprovante_path:
            cursor.execute("""
            UPDATE receitas SET valor = ?, data_pagamento = ?, status = ?, forma_pagamento = ?,
            comprovante_nome = ?, comprovante_path = ?, observacoes = ?
            WHERE id = ?
            """, (valor, data_pagamento, status, forma_pagamento, comprovante_nome, comprovante_path, observacoes, existente["id"]))
        else:
            cursor.execute("""
            UPDATE receitas SET valor = ?, data_pagamento = ?, status = ?, forma_pagamento = ?, observacoes = ?
            WHERE id = ?
            """, (valor, data_pagamento, status, forma_pagamento, observacoes, existente["id"]))
    else:
        cursor.execute("""
        INSERT INTO receitas (casa_id, mes_ano, valor, data_pagamento, status, forma_pagamento, comprovante_nome, comprovante_path, observacoes, criado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (casa_id, mes_ano, valor, data_pagamento, status, forma_pagamento, comprovante_nome, comprovante_path, observacoes, agora))

    conn.commit()
    conn.close()

def get_despesas_mes(mes_ano):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM despesas WHERE mes_ano = ? ORDER BY data_vencimento ASC, id DESC", (mes_ano,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def salvar_despesa(tipo, categoria, descricao, valor, mes_ano, data_vencimento, data_pagamento, status, comprovante_nome=None, comprovante_path=None, observacoes=""):
    conn = get_connection()
    cursor = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO despesas (tipo, categoria, descricao, valor, mes_ano, data_vencimento, data_pagamento, status, comprovante_nome, comprovante_path, observacoes, criado_em)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tipo, categoria, descricao, valor, mes_ano, data_vencimento, data_pagamento, status, comprovante_nome, comprovante_path, observacoes, agora))
    conn.commit()
    conn.close()

def excluir_despesa(despesa_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM despesas WHERE id = ?", (despesa_id,))
    conn.commit()
    conn.close()
