# 🏢 Condomínio Residencial Máximus - Gestão Financeira

Sistema prático para controle de receitas, despesas e geração de balancete mensal para condomínios, desenvolvido em Python e Streamlit com custo zero de infraestrutura.

---

## 🚀 Funcionalidades

1. **Dashboard Mensal:** Visão rápida de receitas realizadas, despesas e taxa de adimplência do condomínio.
2. **Receitas das Unidades:** Registro e baixa dos pagamentos de cota condominial por unidade, com anexo de comprovantes de pagamento (Pix/depósito).
3. **Despesas & Notas Fiscais:** Cadastro de despesas fixas (água, luz, faxina) e variáveis com upload e download de Notas Fiscais, recibos e boletos.
4. **Balancete Oficial (PDF):** Geração instantânea do balancete mensal detalhado em PDF com quadro de assinaturas para o Síndico e Conselho Fiscal.
5. **Configurações:** Cadastro das unidades, moradores, dados do condomínio e upload do logotipo oficial.

---

## 💻 Como Rodar Localmente

1. **Criar e ativar o ambiente virtual (opcional, mas recomendado):**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. **Instalar as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Executar a aplicação:**
   ```bash
   streamlit run app.py
   ```
   A aplicação abrirá automaticamente no seu navegador em `http://localhost:8501`.

---

## ☁️ Como Publicar na Nuvem (Custo R$ 0,00)

1. Envie o projeto para o seu repositório pessoal no **GitHub**.
2. Acesse [share.streamlit.io](https://share.streamlit.io) e faça login com seu GitHub.
3. Clique em **"New app"**, selecione o repositório `maximus` e o arquivo principal `app.py`.
4. Clique em **"Deploy"**! Em menos de 2 minutos você terá um link seguro (ex: `https://condominio-maximus.streamlit.app`) para você e o conselho fiscal acessarem de qualquer computador ou celular.
