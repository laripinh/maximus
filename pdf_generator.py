import os
import io
from datetime import datetime
from fpdf import FPDF
import database as db

class BalancetePDF(FPDF):
    def __init__(self, mes_ano_formatado):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.mes_ano_formatado = mes_ano_formatado
        self.nome_condominio = db.get_config("nome_condominio", "Condomínio Residencial Máximus")
        self.cnpj = db.get_config("cnpj", "")
        self.endereco = db.get_config("endereco", "")

    def header(self):
        # Cabeçalho Elegante
        self.set_fill_color(30, 41, 59) # Slate escuro
        self.rect(0, 0, 210, 28, 'F')
        
        # Verificar se existe logo configurada
        logo_path = os.path.join(os.path.dirname(__file__), "uploads", "logo.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.path.dirname(__file__), "uploads", "logo.jpg")

        x_text = 10
        if os.path.exists(logo_path):
            try:
                self.image(logo_path, x=10, y=4, h=20)
                x_text = 35
            except Exception:
                pass

        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 13)
        self.set_xy(x_text, 5)
        self.cell(200 - x_text, 6, self.nome_condominio.upper(), ln=True, align="L")
        
        self.set_font("Helvetica", "", 7.5)
        subtitulo = []
        if self.cnpj:
            subtitulo.append(f"CNPJ: {self.cnpj}")
        if self.endereco:
            subtitulo.append(self.endereco)
        if subtitulo:
            self.set_xy(x_text, 11)
            self.cell(200 - x_text, 5, " | ".join(subtitulo), ln=True, align="L")
        
        self.set_font("Helvetica", "B", 9.5)
        self.set_xy(x_text, 17)
        self.cell(200 - x_text, 6, f"BALANCETE DE PRESTAÇÃO DE CONTAS - {self.mes_ano_formatado.upper()}", ln=True, align="L")
        
        self.set_text_color(30, 41, 59)
        self.ln(9)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        emissao = datetime.now().strftime("%d/%m/%Y às %H:%M")
        self.cell(0, 10, f"Emissão em {emissao} | Página {self.page_no()}/{{nb}}", align="C")

def format_moeda(valor):
    if valor is None:
        valor = 0.0
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def gerar_balancete_pdf(mes_ano):
    # mes_ano no formato 'YYYY-MM'
    ano, mes = mes_ano.split("-")
    meses_pt = {
        "01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril",
        "05": "Maio", "06": "Junho", "07": "Julho", "08": "Agosto",
        "09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro"
    }
    mes_nome = meses_pt.get(mes, mes)
    mes_ano_formatado = f"{mes_nome} de {ano}"

    receitas = db.get_receitas_mes(mes_ano)
    despesas = db.get_despesas_mes(mes_ano)

    total_receitas = sum(r["valor"] or 0.0 for r in receitas if r.get("status") == "PAGO")
    total_receitas_previstas = sum(r["valor"] or 0.0 for r in receitas)
    total_despesas = sum(d["valor"] or 0.0 for r in despesas if d.get("status") == "PAGO")
    total_despesas_previstas = sum(d["valor"] or 0.0 for r in despesas)
    
    saldo_mes = total_receitas - total_despesas

    pdf = BalancetePDF(mes_ano_formatado)
    pdf.alias_nb_pages()
    pdf.add_page()

    # 1. QUADRO RESUMO FINANCEIRO
    pdf.set_fill_color(241, 245, 249) # Slate claro
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(10, 32, 190, 24, 'FD')

    pdf.set_xy(12, 34)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(60, 4, "TOTAL RECEITAS (ARRECADADO)", align="C")
    pdf.cell(60, 4, "TOTAL DESPESAS (REALIZADO)", align="C")
    pdf.cell(60, 4, "RESULTADO DO MÊS", align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_xy(12, 40)
    pdf.set_text_color(16, 185, 129) # Verde
    pdf.cell(60, 8, format_moeda(total_receitas), align="C")
    
    pdf.set_text_color(239, 68, 68) # Vermelho
    pdf.cell(60, 8, format_moeda(total_despesas), align="C")

    cor_saldo = (16, 185, 129) if saldo_mes >= 0 else (239, 68, 68)
    pdf.set_text_color(*cor_saldo)
    pdf.cell(60, 8, format_moeda(saldo_mes), align="C")
    pdf.ln(18)

    # 2. DEMONSTRATIVO DE RECEITAS (8 CASAS)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 6, "1. DEMONSTRATIVO DE RECEITAS (COTA CONDOMINIAL)", ln=True)

    # Header da tabela de receitas
    pdf.set_fill_color(51, 65, 85)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(20, 6, "UNIDADE", 1, 0, "C", True)
    pdf.cell(65, 6, "MORADOR / RESPONSÁVEL", 1, 0, "L", True)
    pdf.cell(25, 6, "VALOR", 1, 0, "R", True)
    pdf.cell(25, 6, "DATA PGTO", 1, 0, "C", True)
    pdf.cell(25, 6, "FORMA", 1, 0, "C", True)
    pdf.cell(30, 6, "STATUS", 1, 1, "C", True)

    pdf.set_font("Helvetica", "", 8)
    for i, r in enumerate(receitas):
        cor_fundo = 248 if i % 2 == 0 else 255
        pdf.set_fill_color(cor_fundo, cor_fundo, cor_fundo)
        pdf.set_text_color(30, 41, 59)

        ident = r.get("identificacao") or f"Casa {r['numero']:02d}"
        resp = r.get("responsavel") or "-"
        valor = format_moeda(r.get("valor") or 0.0)
        dt = r.get("data_pagamento") or "-"
        forma = r.get("forma_pagamento") or "Pix"
        status = r.get("status") or "PENDENTE"

        pdf.cell(20, 6, ident, 1, 0, "C", True)
        pdf.cell(65, 6, resp[:35], 1, 0, "L", True)
        pdf.cell(25, 6, valor, 1, 0, "R", True)
        pdf.cell(25, 6, dt, 1, 0, "C", True)
        pdf.cell(25, 6, forma, 1, 0, "C", True)

        if status == "PAGO":
            pdf.set_text_color(16, 140, 90)
            pdf.set_font("Helvetica", "B", 8)
        else:
            pdf.set_text_color(220, 38, 38)
            pdf.set_font("Helvetica", "B", 8)
        pdf.cell(30, 6, status, 1, 1, "C", True)
        pdf.set_font("Helvetica", "", 8)

    pdf.ln(5)

    # 3. DEMONSTRATIVO DE DESPESAS
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 6, "2. DEMONSTRATIVO DE DESPESAS (FIXAS E VARIÁVEIS)", ln=True)

    # Header da tabela de despesas
    pdf.set_fill_color(51, 65, 85)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(35, 6, "CATEGORIA", 1, 0, "L", True)
    pdf.cell(65, 6, "DESCRIÇÃO", 1, 0, "L", True)
    pdf.cell(22, 6, "VENCIMENTO", 1, 0, "C", True)
    pdf.cell(22, 6, "PAGAMENTO", 1, 0, "C", True)
    pdf.cell(24, 6, "VALOR", 1, 0, "R", True)
    pdf.cell(22, 6, "DOC/NF", 1, 1, "C", True)

    pdf.set_font("Helvetica", "", 8)
    if not despesas:
        pdf.set_text_color(120, 120, 120)
        pdf.cell(190, 7, "Nenhuma despesa lançada para esta competência.", 1, 1, "C")
    else:
        for i, d in enumerate(despesas):
            cor_fundo = 248 if i % 2 == 0 else 255
            pdf.set_fill_color(cor_fundo, cor_fundo, cor_fundo)
            pdf.set_text_color(30, 41, 59)

            cat = d.get("categoria") or "Geral"
            desc = d.get("descricao") or "-"
            venc = d.get("data_vencimento") or "-"
            pgto = d.get("data_pagamento") or "-"
            val = format_moeda(d.get("valor") or 0.0)
            tem_anexo = "Sim" if d.get("comprovante_nome") else "Não"

            pdf.cell(35, 6, cat[:20], 1, 0, "L", True)
            pdf.cell(65, 6, desc[:36], 1, 0, "L", True)
            pdf.cell(22, 6, venc, 1, 0, "C", True)
            pdf.cell(22, 6, pgto, 1, 0, "C", True)
            pdf.cell(24, 6, val, 1, 0, "R", True)
            pdf.cell(22, 6, tem_anexo, 1, 1, "C", True)

    pdf.ln(10)

    # 4. QUADRO DE ASSINATURAS DO CONSELHO FISCAL
    if pdf.get_y() > 225:
        pdf.add_page()

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 5, "APROVAÇÃO DA PRESTAÇÃO DE CONTAS", ln=True, align="C")
    pdf.set_font("Helvetica", "I", 7.5)
    pdf.cell(0, 4, "Declaramos que conferimos os lançamentos e os respectivos comprovantes e notas fiscais anexos.", ln=True, align="C")
    pdf.ln(10)

    y_pos = pdf.get_y()
    pdf.line(15, y_pos, 95, y_pos)
    pdf.line(115, y_pos, 195, y_pos)

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(30, 41, 59)
    pdf.set_xy(15, y_pos + 1)
    pdf.cell(80, 4, "Síndico(a) / Administrador(a)", align="C")
    pdf.set_xy(115, y_pos + 1)
    pdf.cell(80, 4, "Conselheiro(a) Fiscal 1", align="C")
    pdf.ln(12)

    y_pos2 = pdf.get_y()
    pdf.line(15, y_pos2, 95, y_pos2)
    pdf.line(115, y_pos2, 195, y_pos2)

    pdf.set_xy(15, y_pos2 + 1)
    pdf.cell(80, 4, "Conselheiro(a) Fiscal 2", align="C")
    pdf.set_xy(115, y_pos2 + 1)
    pdf.cell(80, 4, "Conselheiro(a) Fiscal 3", align="C")

    # Retorna os bytes do PDF
    return bytes(pdf.output())
