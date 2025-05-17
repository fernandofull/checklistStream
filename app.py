import streamlit as st
import json
import os

st.set_page_config(page_title="Checklist", layout="centered")

# Função para carregar checklist
CHECKLIST_FILE = 'checklist.json'
def load_checklist():
    if os.path.exists(CHECKLIST_FILE):
        with open(CHECKLIST_FILE, 'r') as f:
            return json.load(f)
    return []

def save_checklist(items):
    with open(CHECKLIST_FILE, 'w') as f:
        json.dump(items, f)

# Inicializar checklist na sessão
if 'checklist' not in st.session_state:
    st.session_state.checklist = load_checklist()

# --- Autenticação simples ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    if st.session_state.get('authenticated'):
        return True
    username = st.sidebar.text_input("Usuário")
    password = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Login"):
        if username == "drld-2025" and password == "drld-2025":
            st.session_state.authenticated = True
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.sidebar.error("Usuário ou senha incorretos")
    return False

st.title("📝 Checklist")

# CSS para melhorar visual e cursor pointer no selectbox
st.markdown('''
    <style>
    .stSelectbox [data-baseweb="select"] {cursor: pointer !important; margin-top: 0 !important;}
    .stSelectbox select {cursor: pointer !important; margin-top: 0 !important;}
    .stSelectbox {display: flex; align-items: center; margin-top: 0 !important;}
    .block-container .stColumns > div {display: flex; align-items: center;}
    </style>
''', unsafe_allow_html=True)

if check_password():
    st.markdown('---')
    # Inicializar estrutura de categorias
    if 'categories' not in st.session_state:
        # Estrutura: {'Comprar': ['item1', 'item2'], ...}
        if os.path.exists('checklist.json'):
            with open('checklist.json', 'r') as f:
                st.session_state.categories = json.load(f)
        else:
            st.session_state.categories = {}

    def save_categories():
        with open('checklist.json', 'w') as f:
            json.dump(st.session_state.categories, f)

    # Selecionar ou criar categoria
    st.subheader('Categorias de Checklist')
    categorias = list(st.session_state.categories.keys())
    categoria = st.selectbox('Selecione uma categoria', categorias + ['+ Nova categoria'])
    if categoria == '+ Nova categoria':
        nova_categoria = st.text_input('Nome da nova categoria')
        if st.button('Criar categoria') and nova_categoria.strip():
            st.session_state.categories[nova_categoria.strip()] = []
            save_categories()
            st.rerun()
        st.stop()

    # Remover categoria com confirmação
    if st.session_state.get('confirm_delete_cat') == categoria:
        st.warning(f'Tem certeza que deseja remover a categoria "{categoria}" e todos os seus itens?')
        col_conf, col_canc = st.columns([0.3, 0.3])
        with col_conf:
            if st.button('Confirmar exclusão', key='confirma_cat'):
                st.session_state.categories.pop(categoria, None)
                save_categories()
                st.session_state['confirm_delete_cat'] = None
                st.rerun()
        with col_canc:
            if st.button('Cancelar', key='cancela_cat'):
                st.session_state['confirm_delete_cat'] = None
                st.rerun()
    else:
        if st.button(f'Remover categoria "{categoria}"', key='remover_categoria', help='Remove toda a categoria e seus itens'):
            st.session_state['confirm_delete_cat'] = categoria
            st.rerun()

    st.markdown('---')
    st.subheader(f'Itens do Checklist: {categoria}')

    # Adicionar itens manualmente
    with st.form(key='add_item_form', clear_on_submit=True):
        novo_item = st.text_input('Adicionar novo item')
        submit_item = st.form_submit_button('Adicionar')
        if submit_item and novo_item.strip():
            st.session_state.categories[categoria].append(novo_item.strip())
            save_categories()
            st.rerun()

    # Adicionar itens por CSV
    import pandas as pd
    uploaded_file = st.file_uploader(
        'Selecione um arquivo CSV',
        type='csv',
        help='A primeira linha deve ser item (rótulo). Cada linha abaixo será um item do checklist.\nExemplo:\nitem\nComprar pão\nLigar para o diretor'
    )
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.write(df)
            if st.button('Importar itens do CSV'):
                col = 'item' if 'item' in df.columns else df.columns[0]
                novos_itens = df[col].dropna().astype(str).tolist()
                # Converter para novo formato se necessário
                novos_itens = [i if isinstance(i, dict) else {"texto": i, "status": "Pendente"} for i in novos_itens]
                st.session_state.categories[categoria].extend(novos_itens)
                save_categories()
                st.success(f'{len(novos_itens)} itens importados!')
                st.rerun()
        except Exception as e:
            st.error(f'Erro ao ler CSV: {e}')

    # Atualizar itens antigos (string) para novo formato
    itens = st.session_state.categories.get(categoria, [])
    for i in range(len(itens)):
        if isinstance(itens[i], str):
            itens[i] = {"texto": itens[i], "status": "Pendente"}
    save_categories()

    if not itens:
        st.info('Nenhum item nesta categoria ainda.')
    else:
        # Cabeçalho alinhado
        cols = st.columns([0.48, 0.26, 0.13, 0.13])
        cols[0].markdown('**Item**')
        cols[1].markdown('**Status**')
        cols[2].markdown('')
        cols[3].markdown('')
        for idx, item in enumerate(itens):
            col1, col2, col3, col4 = st.columns([0.48, 0.26, 0.13, 0.13])
            edit_key = f'edit_{categoria}_{idx}'
            # Texto/edit
            with col1:
                if st.session_state.get(edit_key, False):
                    new_text = st.text_input('Editar item', value=item["texto"], key=f'input_{categoria}_{idx}')
                    save_col, cancel_col = st.columns([0.5, 0.5])
                    with save_col:
                        if st.button('Salvar', key=f'save_{categoria}_{idx}'):
                            item["texto"] = new_text.strip()
                            save_categories()
                            st.session_state[edit_key] = False
                            st.rerun()
                    with cancel_col:
                        if st.button('Cancelar', key=f'cancel_{categoria}_{idx}'):
                            st.session_state[edit_key] = False
                            st.rerun()
                else:
                    st.markdown(item["texto"])
            # Status
            with col2:
                status = st.selectbox(
                    '',
                    ['Pendente', 'Em andamento', 'Concluído'],
                    index=['Pendente', 'Em andamento', 'Concluído'].index(item.get('status', 'Pendente')),
                    key=f'status_{categoria}_{idx}',
                    label_visibility='collapsed'
                )
                if status != item['status']:
                    item['status'] = status
                    save_categories()
            # Editar
            with col3:
                if not st.session_state.get(edit_key, False):
                    if st.button('✏️', key=f'btn_edit_{categoria}_{idx}', help='Editar item'):
                        st.session_state[edit_key] = True
                        st.rerun()
            # Deletar com confirmação
            with col4:
                delete_key = f'confirm_delete_{categoria}_{idx}'
                if st.session_state.get(delete_key, False):
                    st.markdown(
                        '''
                        <div style="display: flex; gap: 8px; align-items: center;">
                            <span style="color:#e74c3c; font-weight:600;">Confirma exclusão?</span>
                        </div>
                        ''',
                        unsafe_allow_html=True
                    )
                    btns = st.columns([1,1])
                    with btns[0]:
                        if st.button('Confirmar', key=f'confirma_item_{categoria}_{idx}'):
                            st.session_state.categories[categoria].pop(idx)
                            save_categories()
                            st.session_state[delete_key] = False
                            st.rerun()
                    with btns[1]:
                        if st.button('Cancelar', key=f'cancela_item_{categoria}_{idx}'):
                            st.session_state[delete_key] = False
                            st.rerun()
                else:
                    if st.button('🗑️', key=f'delete_{categoria}_{idx}'):
                        st.session_state[delete_key] = True
                        st.rerun()