import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import database as db
import pdf_generator as pdf_gen

# Configuração da Página
st.set_page_config(
    page_title="Condomínio Máximus - Gestão Financeira",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar Banco de Dados
db.init_db()

# Criação de pastas de uploads
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
UPLOADS_RECEITAS = os.path.join(UPLOAD_DIR, "receitas")
UPLOADS_DESPESAS = os.path.join(UPLOAD_DIR, "despesas")
os.makedirs(UPLOADS_RECEITAS, exist_ok=True)
os.makedirs(UPLOADS_DESPESAS, exist_ok=True)

def salvar_arquivo(uploaded_file, pasta_destino):
    if not uploaded_file:
        return None, None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_limpo = f"{timestamp}_{uploaded_file.name.replace(' ', '_')}"
    caminho_completo = os.path.join(pasta_destino, nome_limpo)
    with open(caminho_completo, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return uploaded_file.name, caminho_completo

def format_moeda(valor):
    if valor is None:
        valor = 0.0
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# SIDEBAR: Logo, Seletor de Período e Navegação
logo_path = os.path.join(UPLOAD_DIR, "logo.png")
if not os.path.exists(logo_path):
    logo_path = os.path.join(UPLOAD_DIR, "logo.jpg")

if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)
else:
    st.sidebar.image("https://img.icons8.com/fluency/96/condo.png", width=64)

nome_condo_atual = db.get_config("nome_condominio", "Condomínio Máximus")
st.sidebar.title(nome_condo_atual)
st.sidebar.caption("Gestão Financeira e Balancete")

st.sidebar.markdown("---")
# Seleção de Mês e Ano
hoje = date.today()
meses_nomes = [
    ("01", "Janeiro"), ("02", "Fevereiro"), ("03", "Março"), ("04", "Abril"),
    ("05", "Maio"), ("06", "Junho"), ("07", "Julho"), ("08", "Agosto"),
    ("09", "Setembro"), ("10", "Outubro"), ("11", "Novembro"), ("12", "Dezembro")
]

col_m, col_a = st.sidebar.columns(2)
with col_a:
    ano_sel = st.selectbox("Ano", [2024, 2025, 2026, 2027], index=2) # 2026 selecionado
with col_m:
    mes_idx_padrao = hoje.month - 1
    mes_sel = st.selectbox("Mês", options=meses_nomes, format_func=lambda x: x[1], index=mes_idx_padrao)

mes_ano = f"{ano_sel}-{mes_sel[0]}"

menu = st.sidebar.radio(
    "Menu Principal",
    [
        "📊 Dashboard do Mês",
        "💰 Receitas",
        "🧾 Despesas",
        "📄 Balancete",
        "⚙️ Configurações"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(f"📅 **Competência Ativa:**\n{mes_sel[1]} / {ano_sel}")

# ==============================================================================
# 1. DASHBOARD
# ==============================================================================
if menu == "📊 Dashboard do Mês":
    st.title(f"📊 Painel Geral - {mes_sel[1]} de {ano_sel}")
    
    receitas = db.get_receitas_mes(mes_ano)
    despesas = db.get_despesas_mes(mes_ano)
    
    total_unidades = len(receitas) if receitas else 1
    total_arrecadado = sum(r["valor"] or 0.0 for r in receitas if r.get("status") == "PAGO")
    cota_padrao = float(db.get_config("valor_cota_padrao", "300.00"))
    total_previsto = sum(r.get("valor_cota", cota_padrao) for r in receitas)
    
    total_gasto = sum(d["valor"] or 0.0 for d in despesas if d.get("status") == "PAGO")
    saldo_mes = total_arrecadado - total_gasto
    
    pagantes = sum(1 for r in receitas if r.get("status") == "PAGO")
    pendentes = total_unidades - pagantes

    # Métricas Principais
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Arrecadado", format_moeda(total_arrecadado), f"{pagantes}/{total_unidades} quitadas")
    with col2:
        st.metric("Total de Gastos", format_moeda(total_gasto), f"{len(despesas)} despesas")
    with col3:
        cor_delta = "normal" if saldo_mes >= 0 else "inverse"
        st.metric("Saldo do Mês", format_moeda(saldo_mes), "Receitas - Despesas")
    with col4:
        st.metric("Unidades Pendentes", f"{pendentes} pendentes", f"{(pendentes/total_unidades)*100:.0f}% pendência", delta_color="inverse")

    st.markdown("---")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Entradas vs Saídas")
        df_comp = pd.DataFrame([
            {"Tipo": "Arrecadado", "Valor": total_arrecadado},
            {"Tipo": "Gasto", "Valor": total_gasto}
        ])
        fig_bar = px.bar(
            df_comp, x="Tipo", y="Valor", color="Tipo",
            color_discrete_map={"Arrecadado": "#10B981", "Gasto": "#EF4444"},
            text_auto=".2f"
        )
        fig_bar.update_layout(showlegend=False, height=320)
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_g2:
        st.subheader("Despesas por Categoria")
        if despesas:
            df_desp = pd.DataFrame(despesas)
            fig_pie = px.pie(
                df_desp, names="categoria", values="valor",
                color_discrete_sequence=px.colors.qualitative.Safe,
                hole=0.4
            )
            fig_pie.update_layout(height=320)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Nenhuma despesa lançada neste mês.")

# ==============================================================================
# 2. RECEITAS (UNIDADES)
# ==============================================================================
elif menu == "💰 Receitas":
    st.title(f"💰 Receitas do Condomínio - {mes_sel[1]}/{ano_sel}")
    st.write("Acompanhe e dê baixa nos pagamentos da taxa condominial de cada unidade.")

    receitas = db.get_receitas_mes(mes_ano)
    cota_padrao = float(db.get_config("valor_cota_padrao", "300.00"))

    # Grid das unidades
    cols = st.columns(4)
    for idx, r in enumerate(receitas):
        col = cols[idx % 4]
        with col:
            with st.container(border=True):
                num = r["numero"]
                status = r.get("status") or "PENDENTE"
                ident = r.get("identificacao") or f"Casa {num:02d}"
                resp = r.get("responsavel") or "Morador não informado"
                valor_atual = r.get("valor") or r.get("valor_cota", cota_padrao)
                dt_pgto = r.get("data_pagamento") or "-"
                tem_comprovante = bool(r.get("comprovante_nome"))

                if status == "PAGO":
                    st.success(f"### {ident} ✅")
                    st.caption(f"👤 {resp}")
                    st.markdown(f"**Valor Pago:** {format_moeda(valor_atual)}")
                    st.caption(f"🗓️ Data: {dt_pgto} | {r.get('forma_pagamento', 'Boleto')}")
                    if tem_comprovante:
                        st.caption(f"📎 {r['comprovante_nome']}")
                else:
                    st.error(f"### {ident} ⏳")
                    st.caption(f"👤 {resp}")
                    st.markdown(f"**Previsto:** {format_moeda(valor_atual)}")
                    st.warning("Pagamento Pendente")

                # Botão para abrir modal de baixa/edição
                with st.expander(f"Gerenciar {ident}"):
                    with st.form(key=f"form_casa_{num}"):
                        novo_status = st.selectbox("Status", ["PAGO", "PENDENTE"], index=0 if status == "PAGO" else 1)
                        novo_valor = st.number_input("Valor Recebido (R$)", min_value=0.0, value=float(valor_atual), step=10.0)
                        
                        data_padrao = date.today()
                        if r.get("data_pagamento"):
                            try:
                                data_padrao = datetime.strptime(r["data_pagamento"], "%Y-%m-%d").date()
                            except Exception:
                                pass
                        
                        nova_data = st.date_input("Data do Pagamento", value=data_padrao)
                        forma = st.selectbox("Forma de Pagamento", ["Boleto", "Pix", "Transferência", "Dinheiro"], index=0)
                        comprovante = st.file_uploader("Anexar Comprovante (PDF/Foto)", type=["pdf", "png", "jpg", "jpeg"], key=f"up_{num}")
                        obs = st.text_input("Observação", value=r.get("observacoes") or "")

                        salvar = st.form_submit_button("Salvar Pagamento")
                        if salvar:
                            comp_nome = r.get("comprovante_nome")
                            comp_path = r.get("comprovante_path")
                            if comprovante:
                                comp_nome, comp_path = salvar_arquivo(comprovante, UPLOADS_RECEITAS)
                            
                            db.salvar_receita(
                                casa_id=r["casa_id"],
                                mes_ano=mes_ano,
                                valor=novo_valor,
                                data_pagamento=nova_data.strftime("%Y-%m-%d") if novo_status == "PAGO" else None,
                                status=novo_status,
                                forma_pagamento=forma,
                                comprovante_nome=comp_nome,
                                comprovante_path=comp_path,
                                observacoes=obs
                            )
                            st.success(f"Pagamento da {ident} atualizado com sucesso!")
                            st.rerun()

# ==============================================================================
# 3. DESPESAS E NOTAS FISCAIS
# ==============================================================================
elif menu == "🧾 Despesas":
    st.title(f"🧾 Despesas - {mes_sel[1]}/{ano_sel}")
    st.write("Lance os pagamentos fixos (água, luz, zelador) e manutenções avulsas com anexo de notas fiscais.")

    with st.expander("➕ Lançar Nova Despesa / Nota Fiscal", expanded=False):
        with st.form("form_nova_despesa", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                tipo = st.selectbox("Tipo de Despesa", ["FIXA", "VARIAVEL"])
                categoria = st.selectbox(
                    "Categoria",
                    [
                        "Água (Concessionária)",
                        "Energia Elétrica (Concessionária)",
                        "Funcionário / Limpeza / Zelador",
                        "Operadora do Interfone",
                        "Manutenção Portão / Cerca / Câmeras / Interfone",
                        "Material de Limpeza / Jardinagem",
                        "Taxas Bancárias / Tarifas",
                        "Honorários / Assessoria / Contabilidade",
                        "Outros Reparos"
                    ]
                )
                descricao = st.text_input("Descrição / Fornecedor (ex: EMBASA / Neoenergia / Claro)", placeholder="Ex: Conta de água do condomínio")
                valor = st.number_input("Valor da Despesa (R$)", min_value=0.01, step=10.0, format="%.2f")

            with col2:
                dt_venc = st.date_input("Data de Vencimento", value=date.today())
                dt_pgto = st.date_input("Data de Pagamento", value=date.today())
                status_desp = st.selectbox("Status", ["PAGO", "PENDENTE"], index=0)
                arquivo_nf = st.file_uploader("Anexar Nota Fiscal / Boleto / Recibo (PDF/Foto)", type=["pdf", "png", "jpg", "jpeg"])
                obs_desp = st.text_area("Observações adicionais", placeholder="Ex: Pago via Pix pelo Síndico")

            btn_salvar_desp = st.form_submit_button("Salvar Despesa")
            if btn_salvar_desp:
                if not descricao:
                    st.error("Informe a descrição ou fornecedor da despesa.")
                else:
                    nf_nome, nf_path = salvar_arquivo(arquivo_nf, UPLOADS_DESPESAS)
                    db.salvar_despesa(
                        tipo=tipo,
                        categoria=categoria,
                        descricao=descricao,
                        valor=valor,
                        mes_ano=mes_ano,
                        data_vencimento=dt_venc.strftime("%Y-%m-%d"),
                        data_pagamento=dt_pgto.strftime("%Y-%m-%d") if status_desp == "PAGO" else None,
                        status=status_desp,
                        comprovante_nome=nf_nome,
                        comprovante_path=nf_path,
                        observacoes=obs_desp
                    )
                    st.success("Despesa cadastrada com sucesso!")
                    st.rerun()

    st.markdown("---")
    st.subheader(f"Despesas Registradas em {mes_sel[1]}/{ano_sel}")

    despesas = db.get_despesas_mes(mes_ano)
    if not despesas:
        st.info("Nenhuma despesa cadastrada para esta competência.")
    else:
        for d in despesas:
            with st.container(border=True):
                c_info, c_val, c_doc, c_act = st.columns([4, 2, 2, 1])
                with c_info:
                    st.markdown(f"**{d['categoria']}** - {d['descricao']}")
                    st.caption(f"Tipo: {d['tipo']} | Vencimento: {d.get('data_vencimento') or '-'} | Pago em: {d.get('data_pagamento') or '-'}")
                    if d.get("observacoes"):
                        st.caption(f"📝 {d['observacoes']}")
                with c_val:
                    st.markdown(f"### {format_moeda(d['valor'])}")
                    if d.get("status") == "PAGO":
                        st.success("PAGO ✅")
                    else:
                        st.warning("PENDENTE ⏳")
                with c_doc:
                    if d.get("comprovante_nome") and d.get("comprovante_path") and os.path.exists(d["comprovante_path"]):
                        with open(d["comprovante_path"], "rb") as f_anexo:
                            st.download_button(
                                label="📎 Ver Anexo/NF",
                                data=f_anexo.read(),
                                file_name=d["comprovante_nome"],
                                key=f"dl_anexo_{d['id']}"
                            )
                    else:
                        st.caption("Sem anexo")
                with c_act:
                    if st.button("🗑️", key=f"del_{d['id']}", help="Excluir despesa"):
                        db.excluir_despesa(d["id"])
                        st.warning("Despesa excluída!")
                        st.rerun()

# ==============================================================================
# 4. BALANCETE OFICIAL (PDF)
# ==============================================================================
elif menu == "📄 Balancete":
    st.title(f"📄 Balancete de Prestação de Contas")
    st.write(f"Competência: **{mes_sel[1]} de {ano_sel}**")
    st.info("O balancete consolida todas as receitas das unidades e todas as despesas lançadas com assinatura para o Conselho Fiscal.")

    receitas = db.get_receitas_mes(mes_ano)
    despesas = db.get_despesas_mes(mes_ano)

    total_rec = sum(r["valor"] or 0.0 for r in receitas if r.get("status") == "PAGO")
    total_desp = sum(d["valor"] or 0.0 for d in despesas if d.get("status") == "PAGO")
    saldo = total_rec - total_desp

    c1, c2, c3 = st.columns(3)
    c1.metric("Receitas Realizadas", format_moeda(total_rec))
    c2.metric("Despesas Realizadas", format_moeda(total_desp))
    c3.metric("Resultado Final", format_moeda(saldo))

    st.markdown("---")

    # Gerar PDF
    try:
        pdf_bytes = pdf_gen.gerar_balancete_pdf(mes_ano)
        nome_arquivo_pdf = f"Balancete_{mes_sel[1]}_{ano_sel}_Maximus.pdf"

        st.download_button(
            label="📥 Baixar Balancete Oficial em PDF (Pronto para Assinar)",
            data=pdf_bytes,
            file_name=nome_arquivo_pdf,
            mime="application/pdf",
            type="primary"
        )
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}")

    st.markdown("---")
    st.subheader("Prévia dos Lançamentos")
    tab_r, tab_d = st.tabs(["Receitas das Unidades", "Despesas do Mês"])
    with tab_r:
        df_r = pd.DataFrame(receitas)[["numero", "identificacao", "responsavel", "valor", "data_pagamento", "forma_pagamento", "status"]]
        df_r.columns = ["Nº", "Unidade", "Morador", "Valor (R$)", "Data Pgto", "Forma", "Status"]
        st.dataframe(df_r, use_container_width=True, hide_index=True)
    with tab_d:
        if despesas:
            df_d = pd.DataFrame(despesas)[["categoria", "descricao", "valor", "data_vencimento", "data_pagamento", "status"]]
            df_d.columns = ["Categoria", "Descrição", "Valor (R$)", "Vencimento", "Pagamento", "Status"]
            st.dataframe(df_d, use_container_width=True, hide_index=True)
        else:
            st.write("Nenhuma despesa lançada.")

# ==============================================================================
# 5. CONFIGURAÇÕES
# ==============================================================================
elif menu == "⚙️ Configurações":
    st.title("⚙️ Configurações do Condomínio")

    tab_geral, tab_casas, tab_limpeza = st.tabs(["Dados do Condomínio", "Cadastro das Unidades", "Dados de Teste e Limpeza"])

    with tab_geral:
        col_dados, col_logo = st.columns([3, 2])
        with col_dados:
            with st.form("form_config_geral"):
                nome = st.text_input("Nome do Condomínio", value=db.get_config("nome_condominio", "Condomínio Residencial Máximus"))
                cnpj = st.text_input("CNPJ (opcional)", value=db.get_config("cnpj", ""))
                endereco = st.text_input("Endereço Completo", value=db.get_config("endereco", ""))
                cota_padrao = st.number_input("Valor Padrão da Cota Condominial (R$)", min_value=0.0, value=float(db.get_config("valor_cota_padrao", "300.00")), step=10.0)
                
                salvar_cfg = st.form_submit_button("Salvar Dados Gerais")
                if salvar_cfg:
                    db.set_config("nome_condominio", nome)
                    db.set_config("cnpj", cnpj)
                    db.set_config("endereco", endereco)
                    db.set_config("valor_cota_padrao", str(cota_padrao))
                    st.success("Configurações salvas com sucesso!")
                    st.rerun()

        with col_logo:
            st.markdown("#### Logotipo / Foto do Condomínio")
            if os.path.exists(logo_path):
                st.image(logo_path, caption="Logo Atual", width=180)
            
            nova_logo = st.file_uploader("Enviar nova foto/logo (PNG ou JPG)", type=["png", "jpg", "jpeg"])
            if nova_logo is not None:
                if st.button("Aplicar Logotipo"):
                    ext = nova_logo.name.split(".")[-1].lower()
                    target_logo = os.path.join(UPLOAD_DIR, "logo.png")
                    with open(target_logo, "wb") as f_logo:
                        f_logo.write(nova_logo.getbuffer())
                    st.success("Logo atualizada! Aparecerá no menu lateral e no cabeçalho do PDF.")
                    st.rerun()

    with tab_casas:
        st.write("Edite os nomes dos responsáveis e contatos de cada unidade:")
        casas = db.get_todas_casas()
        for c in casas:
            with st.expander(f"Editar {c['identificacao']} (Unidade {c['numero']:02d})"):
                with st.form(f"form_casa_edit_{c['id']}"):
                    novo_ident = st.text_input("Identificação (ex: Casa 01, Apto 101)", value=c["identificacao"])
                    novo_resp = st.text_input("Nome do Responsável / Morador", value=c["responsavel"] or "")
                    novo_contato = st.text_input("Telefone / WhatsApp", value=c["contato"] or "")
                    novo_valor = st.number_input("Valor da Cota desta Unidade (R$)", min_value=0.0, value=float(c.get("valor_cota") or 300.00), step=10.0)
                    
                    if st.form_submit_button("Atualizar Unidade"):
                        conn = db.get_connection()
                        conn.cursor().execute("""
                        UPDATE casas SET identificacao = ?, responsavel = ?, contato = ?, valor_cota = ? WHERE id = ?
                        """, (novo_ident, novo_resp, novo_contato, novo_valor, c["id"]))
                        conn.commit()
                        conn.close()
                        st.success(f"{novo_ident} atualizada com sucesso!")
                        st.rerun()

    with tab_limpeza:
        st.subheader("🧹 Limpeza de Dados de Teste")
        st.write(
            "Use esta opção enquanto estiver testando o sistema. "
            "Você pode lançar pagamentos, despesas e anexar comprovantes de teste à vontade. "
            "Quando estiver pronto para iniciar o uso oficial do condomínio, basta zerar as movimentações."
        )

        with st.container(border=True):
            st.markdown("⚠️ **Atenção:**")
            st.markdown(
                "- Esta ação **apaga todos os lançamentos de receitas e despesas**.\n"
                "- Esta ação **remove os comprovantes e notas anexadas** durante o teste.\n"
                "- Os dados do condomínio (nome, endereço) e o cadastro dos moradores **NÃO serão apagados**."
            )
            
            confirmar = st.checkbox("Confirmo que desejo apagar todas as movimentações e comprovantes de teste.")
            
            if st.button("🗑️ Zerar Lançamentos de Teste", type="primary", disabled=not confirmar):
                db.zerar_lancamentos(limpar_arquivos=True)
                st.success("✨ Todos os dados de teste foram apagados com sucesso! O sistema está limpo para o uso oficial.")
                st.rerun()
