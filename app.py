import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
import requests

# CONFIGURAÇÃO INICIAL
st.set_page_config(
    page_title='Telemarketing analysis',
    page_icon='https://github.com/JoaoPauloCosta812/Marketing-Base-Ciencia-de-Dados/blob/main/img/telmarketing_icon.png?raw=true',
    layout="wide",
    initial_sidebar_state='expanded'
)

# Tema visual
custom_params = {"axes.spines.right": False, "axes.spines.top": False}
sns.set_theme(style="ticks", rc=custom_params)

# FUNÇÕES COM CACHE AJUSTADO

@st.cache_data(show_spinner=True)
def load_data(file_data):
    """Lê arquivo CSV ou Excel."""
    try:
        return pd.read_csv(file_data, sep=';')
    except:
        return pd.read_excel(file_data)

@st.cache_data
def multiselect_filter(relatorio, col, selecionados):
    """Filtra dataframe com base em colunas selecionadas."""
    if 'all' in selecionados:
        return relatorio
    else:
        return relatorio[relatorio[col].isin(selecionados)].reset_index(drop=True)

@st.cache_data
def convert_df(df):
    """Converte dataframe para CSV."""
    return df.to_csv(index=False).encode('utf-8')

@st.cache_data
def to_excel(df):
    """Converte dataframe para arquivo Excel."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# FUNÇÃO PRINCIPAL
def main():
    st.write('# Telemarketing analysis')
    st.markdown("---")

    # Sidebar - imagem
    try:
        url_img = "https://raw.githubusercontent.com/JoaoPauloCosta812/Marketing-Base-Ciencia-de-Dados/main/img/bank_img.png"
        r = requests.get(url_img, timeout=10)
        r.raise_for_status()
        image = Image.open(BytesIO(r.content))
        st.sidebar.image(image)  # <- sem use_container_width
    except Exception as e:
        st.sidebar.warning(f"Imagem não encontrada. Detalhe: {e}")

    # Upload de arquivo
    st.sidebar.write("## Suba o arquivo")
    data_file_1 = st.sidebar.file_uploader("Bank marketing data", type=['csv', 'xlsx'])

    if data_file_1 is not None:
        bank_raw = load_data(data_file_1)
        bank = bank_raw.copy()

        st.write('## Antes dos filtros')
        st.write(bank_raw.head())
        st.markdown("---")

        # Sidebar de filtros
        with st.sidebar.form(key='filters_form'):
            graph_type = st.radio('Tipo de gráfico:', ('Barras', 'Pizza'))

            # Filtro por idade
            min_age = int(bank.age.min())
            max_age = int(bank.age.max())
            idades = st.slider('Idade', min_value=min_age, max_value=max_age, value=(min_age, max_age), step=1)

            # Função auxiliar para criar multiselect com a opção 'all'
            def create_multiselect(label, column):
                items = bank[column].unique().tolist()
                items.append('all')
                return st.multiselect(label, items, default=['all'])

            jobs_selected = create_multiselect("Profissão", 'job')
            marital_selected = create_multiselect("Estado civil", 'marital')
            default_selected = create_multiselect("Default", 'default')
            housing_selected = create_multiselect("Financiamento Imobiliário", 'housing')
            loan_selected = create_multiselect("Empréstimo", 'loan')
            contact_selected = create_multiselect("Meio de contato", 'contact')
            month_selected = create_multiselect("Mês do contato", 'month')
            day_of_week_selected = create_multiselect("Dia da semana", 'day_of_week')

            # Aplicação dos filtros
            bank = (
                bank.query("age >= @idades[0] and age <= @idades[1]")
                .pipe(multiselect_filter, 'job', jobs_selected)
                .pipe(multiselect_filter, 'marital', marital_selected)
                .pipe(multiselect_filter, 'default', default_selected)
                .pipe(multiselect_filter, 'housing', housing_selected)
                .pipe(multiselect_filter, 'loan', loan_selected)
                .pipe(multiselect_filter, 'contact', contact_selected)
                .pipe(multiselect_filter, 'month', month_selected)
                .pipe(multiselect_filter, 'day_of_week', day_of_week_selected)
            )

            submitted = st.form_submit_button("Aplicar filtros")

        st.write('## Após os filtros')
        st.write(bank.head())

        # Download dos dados filtrados
        df_xlsx = to_excel(bank)
        st.download_button(
            label='📥 Download tabela filtrada em EXCEL',
            data=df_xlsx,
            file_name='bank_filtered.xlsx'
        )
        st.markdown("---")

        bank_raw_target_perc = (
            bank_raw.y.value_counts(normalize=True)
            .mul(100)
            .rename_axis('Resposta')
            .reset_index(name='Percentual')
        )

        bank_target_perc = (
            bank.y.value_counts(normalize=True)
            .mul(100)
            .rename_axis('Resposta')
            .reset_index(name='Percentual')
        )

        col1, col2 = st.columns(2)

        df_xlsx = to_excel(bank_raw_target_perc)
        col1.write('### Proporção original')
        col1.write(bank_raw_target_perc)
        col1.download_button(label='📥 Download',
                             data= df_xlsx,
                             file_name= 'bank_raw_y.xlsx')
        
        df_xlsx = to_excel(bank_target_perc)
        col2.write('### Proporção com filtros')
        col2.write(bank_target_perc)
        col2.download_button(label='📥 Download',
                             data= df_xlsx,
                             file_name= 'bank_y.xlsx')
        st.markdown("---")

        st.write('## Proporção de aceite')
        fig, ax = plt.subplots(1, 2, figsize=(8, 4))


        # GRÁFICOS
        if graph_type == 'Barras':
            sns.barplot(
                x='Resposta', y='Percentual', data=bank_raw_target_perc, ax=ax[0]
            )
            ax[0].bar_label(ax[0].containers[0], fmt='%.2f%%')
            ax[0].set_title('Dados brutos', fontweight='bold')
            ax[0].set_xlabel('')
            ax[0].set_ylabel('Percentual (%)')

            sns.barplot(
                x='Resposta', y='Percentual', data=bank_target_perc, ax=ax[1]
            )
            ax[1].bar_label(ax[1].containers[0], fmt='%.2f%%')
            ax[1].set_title('Dados filtrados', fontweight='bold')
            ax[1].set_xlabel('')
            ax[1].set_ylabel('')
        else:
            bank_raw_target_perc.set_index('Resposta').plot(
                kind='pie', y='Percentual', autopct='%.2f%%', ax=ax[0], legend=False
            )
            ax[0].set_ylabel('')
            ax[0].set_title('Dados brutos', fontweight='bold')

            bank_target_perc.set_index('Resposta').plot(
                kind='pie', y='Percentual', autopct='%.2f%%', ax=ax[1], legend=False
            )
            ax[1].set_ylabel('')
            ax[1].set_title('Dados filtrados', fontweight='bold')

        st.pyplot(fig)

# EXECUÇÃO
if __name__ == '__main__':
    main()













