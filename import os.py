import os
import fdb
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import urllib.request
import time
import pickle
from pathlib import Path
from collections import deque

# Cache de CNPJs consultados (no início do arquivo, após imports)
CACHE_FILE = Path.home() / ".cache_cnpj.pkl"
_cache_cnpj = {}

def _carregar_cache():
    global _cache_cnpj
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'rb') as f:
                _cache_cnpj = pickle.load(f)
        except:
            _cache_cnpj = {}

def _salvar_cache():
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(_cache_cnpj, f)
    except:
        pass

# Carregar cache ao iniciar
_carregar_cache()

def get_connection(
    host=os.getenv("FB_HOST", "localhost"),
    port=os.getenv("FB_PORT", "3050"),
    user=os.getenv("FB_USER", "SYSDBA"),
    password=os.getenv("FB_PASSWORD", "masterkey"),
    database=os.getenv("FB_DATABASE", r"C:\data\example.fdb"),
):
    dsn = f"{host}/{port}:{database}" if host else database
    return fdb.connect(dsn=dsn, user=user, password=password)

def fetch_people(con, filtro_nome=""):
    cur = con.cursor()
    try:
        if filtro_nome:
            cur.execute(
                """
                SELECT P.*, R.DESC_ROYALTIES AS ROYALTIES_DESCRICAO
                FROM PESSOA P
                LEFT JOIN PESAGEM_ROYALTIES R
                       ON R.COD_ROYALTIES = P.ID_ROYALTIES
                WHERE P.NOME CONTAINING ?
                """,
                (filtro_nome,),
            )
        else:
            cur.execute(
                """
                SELECT P.*, R.DESC_ROYALTIES AS ROYALTIES_DESCRICAO
                FROM PESSOA P
                LEFT JOIN PESAGEM_ROYALTIES R
                       ON R.COD_ROYALTIES = P.ID_ROYALTIES
                """
            )
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        return columns, rows
    except Exception:
        pass

    tabelas_royaltie = ["ROYALTIES", "ROYALTIE", "CAD_ROYALTIES", "ROYALTY"]
    colunas_desc = ["DESCRICAO", "NOME", "DESCR", "DESCRICAO_ROYALTIES"]

    for tabela in tabelas_royaltie:
        for col_desc in colunas_desc:
            try:
                if filtro_nome:
                    cur.execute(
                        f"""
                        SELECT P.*, R.{col_desc} AS ROYALTIES_DESCRICAO
                        FROM PESSOA P
                        LEFT JOIN {tabela} R ON R.ID_ROYALTIES = P.ID_ROYALTIES
                        WHERE P.NOME CONTAINING ?
                        """,
                        (filtro_nome,),
                    )
                else:
                    cur.execute(
                        f"""
                        SELECT P.*, R.{col_desc} AS ROYALTIES_DESCRICAO
                        FROM PESSOA P
                        LEFT JOIN {tabela} R ON R.ID_ROYALTIES = P.ID_ROYALTIES
                        """
                    )
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                return columns, rows
            except Exception:
                continue

    if filtro_nome:
        cur.execute("SELECT * FROM PESSOA WHERE NOME CONTAINING ?", (filtro_nome,))
    else:
        cur.execute("SELECT * FROM PESSOA")
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    return columns, rows

def _somente_digitos(valor):
    return "".join(ch for ch in str(valor or "") if ch.isdigit())

def validar_cpf(cpf):
    cpf = _somente_digitos(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma1 * 10) % 11
    d1 = 0 if d1 == 10 else d1
    if d1 != int(cpf[9]):
        return False
    soma2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (soma2 * 10) % 11
    d2 = 0 if d2 == 10 else d2
    return d2 == int(cpf[10])

def validar_cnpj(cnpj):
    cnpj = _somente_digitos(cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma1 = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    d1 = 11 - (soma1 % 11)
    d1 = 0 if d1 >= 10 else d1
    if d1 != int(cnpj[12]):
        return False
    soma2 = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    d2 = 11 - (soma2 % 11)
    d2 = 0 if d2 >= 10 else d2
    return d2 == int(cnpj[13])

def analisar_problemas(columns, rows):
    idx = {c: i for i, c in enumerate(columns)}
    get = lambda r, c: r[idx[c]] if c in idx else None

    def _is_ativo(r):
        if "SITUACAO" in idx:
            return str(get(r, "SITUACAO") or "").strip().upper() != "I"
        if "CADASTRO_VALIDO" in idx:
            return str(get(r, "CADASTRO_VALIDO") or "").strip().upper() != "N"
        return True

    # índices principais
    problemas = []
    cpfs = {}
    cnpjs = {}

    for r in rows:
        if not _is_ativo(r):
            continue
        cpf_raw = get(r, "CPF")
        cnpj_raw = get(r, "CGC")
        cpf = _somente_digitos(cpf_raw)
        cnpj = _somente_digitos(cnpj_raw)

        if cpf:
            cpfs[cpf] = cpfs.get(cpf, 0) + 1
        if cnpj:
            cnpjs[cnpj] = cnpjs.get(cnpj, 0) + 1

    for r in rows:
        if not _is_ativo(r):
            continue
        cod = get(r, "CODPESSOA")
        nome = get(r, "NOME")
        tipo = (get(r, "TIPO") or "").strip().upper()
        cpf_raw = get(r, "CPF")
        cnpj_raw = get(r, "CGC")

        cpf = _somente_digitos(cpf_raw)
        cnpj = _somente_digitos(cnpj_raw)

        erros = []

        if not str(nome or "").strip():
            erros.append("Nome vazio")

        if cpf and not validar_cpf(cpf):
            erros.append("CPF inválido")
        if cnpj and not validar_cnpj(cnpj):
            erros.append("CNPJ inválido")

        if cpf and cpfs.get(cpf, 0) > 1:
            erros.append("CPF duplicado")
        if cnpj and cnpjs.get(cnpj, 0) > 1:
            erros.append("CNPJ duplicado")

        if tipo == "F":
            if cnpj:
                erros.append("Tipo F com CNPJ informado")
            if cpf and not validar_cpf(cpf):
                erros.append("Tipo F com CPF inválido")
        elif tipo == "J":
            if cpf:
                erros.append("Tipo J com CPF informado")
            if cnpj and not validar_cnpj(cnpj):
                erros.append("Tipo J com CNPJ inválido")
        else:
            erros.append("Tipo de cadastro não informado")

        if erros:
            problemas.append((cod, nome, tipo, cpf or cnpj or "", " / ".join(erros)))

    return problemas

def _limpar_documento(valor):
    doc = _somente_digitos(valor)
    return doc if doc else None

def sugerir_ajustes_massa(columns, rows):
    idx = {c: i for i, c in enumerate(columns)}
    get = lambda r, c: r[idx[c]] if c in idx else None

    def _is_ativo(r):
        if "SITUACAO" in idx:
            return str(get(r, "SITUACAO") or "").strip().upper() != "I"
        if "CADASTRO_VALIDO" in idx:
            return str(get(r, "CADASTRO_VALIDO") or "").strip().upper() != "N"
        return True

    sugestoes = []

    def add(cod, campo, valor, motivo):
        if cod is None:
            return
        sugestoes.append((cod, campo, valor, motivo))

    for r in rows:
        if not _is_ativo(r):
            continue

        cod = get(r, "CODPESSOA")
        nome = get(r, "NOME")
        nomefantasia = get(r, "NOMEFANTASIA")
        tipo = (get(r, "TIPO") or "").strip().upper()

        cpf_raw = get(r, "CPF")
        cnpj_raw = get(r, "CGC")

        cpf = _limpar_documento(cpf_raw)
        cnpj = _limpar_documento(cnpj_raw)

        if not str(nome or "").strip() and str(nomefantasia or "").strip():
            add(cod, "NOME", str(nomefantasia).strip(), "Nome vazio; usar Nome fantasia")

        if cpf_raw and cpf and str(cpf_raw).strip() != cpf:
            add(cod, "CPF", cpf, "Normalizar CPF (remover caracteres)")
        if cnpj_raw and cnpj and str(cnpj_raw).strip() != cnpj:
            add(cod, "CGC", cnpj, "Normalizar CNPJ (remover caracteres)")

        if tipo == "F" and cnpj_raw:
            add(cod, "CGC", None, "Tipo F não deve ter CNPJ")
        if tipo == "J" and cpf_raw:
            add(cod, "CPF", None, "Tipo J não deve ter CPF")

    return sugestoes

def launch_gui():
    root = tk.Tk()
    root.title("Sistema de Gestão de Cadastros - Firebird")
    root.state('zoomed')  # Maximizar janela

    fields = {
        "Host": os.getenv("FB_HOST", "localhost"),
        "Porta": os.getenv("FB_PORT", "3050"),
        "Usuário": os.getenv("FB_USER", "SYSDBA"),
        "Senha": os.getenv("FB_PASSWORD", "masterkey"),
        "Database": os.getenv("FB_DATABASE", r"C:\data\example.fdb"),
    }

    entries = {}
    for i, (label, value) in enumerate(fields.items()):
        ttk.Label(root, text=label).grid(row=i, column=0, padx=8, pady=4, sticky="w")
        show = "*" if label == "Senha" else ""
        entry = ttk.Entry(root, width=40, show=show)
        entry.insert(0, value)
        entry.grid(row=i, column=1, padx=8, pady=4, sticky="ew")
        entries[label] = entry

        if label == "Database":
            def on_browse():
                path = filedialog.askopenfilename(
                    title="Selecionar base Firebird",
                    filetypes=[("Firebird DB", "*.fdb"), ("Todos os arquivos", "*")]
                )
                if path:
                    entries["Database"].delete(0, tk.END)
                    entries["Database"].insert(0, path)

            ttk.Button(root, text="Procurar...", command=on_browse).grid(
                row=i, column=2, padx=8, pady=4, sticky="w"
            )

    status_var = tk.StringVar(value="Aguardando conexão...")
    api_url_var = tk.StringVar(value=API_URL_TEMPLATE)

    def testar_conexao():
        try:
            con = get_connection(
                entries["Host"].get().strip(),
                entries["Porta"].get().strip(),
                entries["Usuário"].get().strip(),
                entries["Senha"].get(),
                entries["Database"].get().strip(),
            )
            con.close()
            status_var.set("Conexão realizada com sucesso.")
        except Exception as e:
            status_var.set(f"Falha na conexão: {e}")

    style = ttk.Style(root)
    style.configure("Destaque.TButton", font=("Segoe UI", 10, "bold"))

    actions_frame = ttk.Frame(root)
    actions_frame.grid(row=len(fields), column=0, columnspan=3, sticky="ew", padx=8, pady=6)
    actions_frame.columnconfigure(1, weight=1)

    ttk.Button(actions_frame, text="Conectar", style="Destaque.TButton", command=testar_conexao).grid(
        row=0, column=0, padx=(0, 8)
    )
    ttk.Label(actions_frame, textvariable=status_var).grid(
        row=0, column=1, sticky="w"
    )

    root.columnconfigure(1, weight=1)

    notebook = ttk.Notebook(root)
    notebook.grid(row=len(fields) + 1, column=0, columnspan=3, sticky="nsew", padx=8, pady=6)

    # Criar todas as abas
    pessoas_tab = ttk.Frame(notebook)
    massa_tab = ttk.Frame(notebook)
    problemas_tab = ttk.Frame(notebook)
    duplicados_tab = ttk.Frame(notebook)  # Nova aba para duplicados
    api_tab = ttk.Frame(notebook)
    validacao_tab = ttk.Frame(notebook)  # Nova aba para validação
    relatorios_tab = ttk.Frame(notebook)  # Nova aba para relatórios
    
    notebook.add(pessoas_tab, text="📋 Pessoas")
    notebook.add(validacao_tab, text="✅ Validação")
    notebook.add(duplicados_tab, text="👥 Duplicados")
    notebook.add(problemas_tab, text="⚠️ Problemas")
    notebook.add(api_tab, text="🌐 Atualizar via API")
    notebook.add(massa_tab, text="⚡ Atualização em Massa")
    notebook.add(relatorios_tab, text="📊 Relatórios")

    pessoas_tab.columnconfigure(0, weight=1)
    pessoas_tab.rowconfigure(1, weight=1)

    filtro_frame = ttk.Frame(pessoas_tab)
    filtro_frame.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
    filtro_frame.columnconfigure(1, weight=1)

    ttk.Label(filtro_frame, text="Pesquisar por nome:").grid(row=0, column=0, padx=4, sticky="w")
    filtro_var = tk.StringVar()
    ttk.Entry(filtro_frame, textvariable=filtro_var).grid(row=0, column=1, padx=4, sticky="ew")

    table_frame = ttk.Frame(pessoas_tab)
    table_frame.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)

    tree = ttk.Treeview(table_frame, show="headings")
    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    table_frame.columnconfigure(0, weight=1)
    table_frame.rowconfigure(0, weight=1)

    edit_frame = ttk.LabelFrame(pessoas_tab, text="Edição individual")
    edit_frame.grid(row=2, column=0, sticky="ew", padx=4, pady=4)
    edit_frame.columnconfigure(0, minsize=130)
    edit_frame.columnconfigure(2, minsize=130)
    edit_frame.columnconfigure(1, weight=1)
    edit_frame.columnconfigure(3, weight=1)

    campos_edicao = [
        ("CODPESSOA", "Código"),
        ("NOME", "Nome"),
        ("NOMEFANTASIA", "Nome fantasia"),
        ("EMAIL", "E-mail"),
        ("FONE1", "Fone"),
        ("ID_ROYALTIES", "Royalties (ID)"),
        ("ROYALTIES_DESCRICAO", "Royalties (descrição)"),
    ]
    edit_vars = {c: tk.StringVar() for c, _ in campos_edicao}

    for i, (campo, label) in enumerate(campos_edicao):
        row, col = divmod(i, 2)
        ttk.Label(edit_frame, text=label).grid(row=row, column=col * 2, padx=4, pady=2, sticky="w")
        ent = ttk.Entry(edit_frame, textvariable=edit_vars[campo])
        ent.grid(row=row, column=col * 2 + 1, padx=4, pady=2, sticky="ew")
        if campo in ("CODPESSOA", "ROYALTIES_DESCRICAO"):
            ent.configure(state="readonly")

    def carregar_selecao(_=None):
        sel = tree.selection()
        if not sel:
            return
        values = tree.item(sel[0], "values")
        col_map = {col: i for i, col in enumerate(tree["columns"])}
        for campo, _ in campos_edicao:
            if campo in col_map:
                edit_vars[campo].set(values[col_map[campo]])

    def atualizar_individual():
        cod = edit_vars["CODPESSOA"].get().strip()
        if not cod:
            messagebox.showwarning("Atenção", "Selecione um registro.")
            return
        try:
            con = get_connection(
                entries["Host"].get().strip(),
                entries["Porta"].get().strip(),
                entries["Usuário"].get().strip(),
                entries["Senha"].get(),
                entries["Database"].get().strip(),
            )
            try:
                cur = con.cursor()
                cur.execute(
                    """
                    UPDATE PESSOA
                    SET NOME=?, NOMEFANTASIA=?, EMAIL=?, FONE1=?, ID_ROYALTIES=?
                    WHERE CODPESSOA=?
                    """,
                    (
                        edit_vars["NOME"].get().strip(),
                        edit_vars["NOMEFANTASIA"].get().strip(),
                        edit_vars["EMAIL"].get().strip(),
                        edit_vars["FONE1"].get().strip(),
                        edit_vars["ID_ROYALTIES"].get().strip() or None,
                        int(cod),
                    ),
                )
                con.commit()
            finally:
                con.close()
            on_load()
            status_var.set("Registro atualizado com sucesso.")
        except Exception as e:
            status_var.set(f"Falha ao atualizar: {e}")

    def _campo_inativacao_disponivel(columns):
        if "SITUACAO" in columns:
            return ("SITUACAO", "I", "A")
        if "CADASTRO_VALIDO" in columns:
            return ("CADASTRO_VALIDO", "N", "S")
        return None

    def abrir_configuracoes():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um registro.")
            return

        columns = list(tree["columns"])
        values = tree.item(sel[0], "values")
        col_map = {col: i for i, col in enumerate(columns)}
        cod = values[col_map["CODPESSOA"]] if "CODPESSOA" in col_map else ""
        nome = values[col_map["NOME"]] if "NOME" in col_map else ""

        top = tk.Toplevel(root)
        top.title(f"Configurações do cadastro - {cod} {nome}")
        top.geometry("700x500")

        ttk.Label(top, text="Dados completos do cadastro:").pack(anchor="w", padx=10, pady=(10, 4))
        txt = tk.Text(top, height=18, wrap="none")
        txt.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        for col in columns:
            val = values[col_map[col]] if col in col_map else ""
            txt.insert(tk.END, f"{col}: {val}\n")
        txt.configure(state="disabled")

        inativacao = _campo_inativacao_disponivel(columns)
        inativo_var = tk.BooleanVar(value=False)

        if inativacao:
            campo, val_inativo, val_ativo = inativacao
            atual = values[col_map[campo]] if campo in col_map else ""
            inativo_var.set(str(atual).strip().upper() == str(val_inativo).upper())
            ttk.Checkbutton(top, text="Inativar cadastro", variable=inativo_var).pack(
                anchor="w", padx=10, pady=(4, 8)
            )
        else:
            ttk.Label(
                top,
                text="Campo de inativação não encontrado (SITUACAO ou CADASTRO_VALIDO).",
                foreground="red",
            ).pack(anchor="w", padx=10, pady=(4, 8))

        def salvar_configuracoes():
            if not inativacao:
                return
            campo, val_inativo, val_ativo = inativacao
            try:
                con = get_connection(
                    entries["Host"].get().strip(),
                    entries["Porta"].get().strip(),
                    entries["Usuário"].get().strip(),
                    entries["Senha"].get(),
                    entries["Database"].get().strip(),
                )
                try:
                    cur = con.cursor()
                    cur.execute(
                        f"UPDATE PESSOA SET {campo}=? WHERE CODPESSOA=?",
                        (
                            val_inativo if inativo_var.get() else val_ativo,
                            int(cod),
                        ),
                    )
                    con.commit()
                finally:
                    con.close()
                on_load()
                status_var.set("Configurações salvas com sucesso.")
                top.destroy()
            except Exception as e:
                status_var.set(f"Falha ao salvar configurações: {e}")

        ttk.Button(top, text="Salvar configurações", command=salvar_configuracoes).pack(
            anchor="e", padx=10, pady=10
        )

    def clonar_registro():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um registro para clonar.")
            return

        columns = list(tree["columns"])
        values = tree.item(sel[0], "values")
        col_map = {col: i for i, col in enumerate(columns)}
        cod = values[col_map["CODPESSOA"]] if "CODPESSOA" in col_map else ""

        top = tk.Toplevel(root)
        top.title(f"Clonar registro - {cod}")
        top.geometry("500x380")
        top.grab_set()
        top.columnconfigure(1, weight=1)

        campos_clonar = [
            ("NOME", "Nome"),
            ("NOMEFANTASIA", "Nome fantasia"),
            ("EMAIL", "E-mail"),
            ("FONE1", "Fone"),
            ("ID_ROYALTIES", "Royalties (ID)"),
        ]

        clone_vars = {}
        for i, (campo, label) in enumerate(campos_clonar):
            ttk.Label(top, text=label).grid(row=i, column=0, padx=8, pady=4, sticky="w")
            var = tk.StringVar()
            if campo in col_map:
                valor = values[col_map[campo]]
                var.set(valor if valor is not None else "")
            clone_vars[campo] = var
            ttk.Entry(top, textvariable=var, width=40).grid(row=i, column=1, padx=8, pady=4, sticky="ew")

        ttk.Label(
            top,
            text="⚠️ CPF e CNPJ não serão copiados (devem ser únicos).",
            foreground="orange",
        ).grid(row=len(campos_clonar), column=0, columnspan=2, padx=8, pady=6)

        def confirmar_clone():
            try:
                con = get_connection(
                    entries["Host"].get().strip(),
                    entries["Porta"].get().strip(),
                    entries["Usuário"].get().strip(),
                    entries["Senha"].get(),
                    entries["Database"].get().strip(),
                )
                try:
                    cur = con.cursor()
                    campos_insert = [c for c, _ in campos_clonar]
                    vals = []
                    for c in campos_insert:
                        v = clone_vars[c].get().strip()
                        vals.append(v if v else None)
                    placeholders = ", ".join(["?" for _ in campos_insert])
                    campos_str = ", ".join(campos_insert)
                    cur.execute(
                        f"INSERT INTO PESSOA ({campos_str}) VALUES ({placeholders})",
                        tuple(vals),
                    )
                    con.commit()
                finally:
                    con.close()
                on_load()
                status_var.set("Registro clonado com sucesso.")
                top.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao clonar registro: {e}")
                status_var.set(f"Falha ao clonar registro: {e}")

        btn_frame = ttk.Frame(top)
        btn_frame.grid(row=len(campos_clonar) + 1, column=0, columnspan=2, pady=8)
        ttk.Button(btn_frame, text="✅ Confirmar clone", command=confirmar_clone).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Cancelar", command=top.destroy).pack(side="left", padx=4)

    ttk.Button(edit_frame, text="Atualizar registro", command=atualizar_individual).grid(
        row=2, column=0, columnspan=4, pady=6
    )
    ttk.Button(edit_frame, text="Configurações do cadastro", command=abrir_configuracoes).grid(
        row=3, column=0, columnspan=4, pady=4
    )
    ttk.Button(edit_frame, text="🔁 Clonar registro", command=clonar_registro).grid(
        row=5, column=0, columnspan=4, pady=4
    )

    def _buscar_cgc_por_cod(cod):
        con = get_connection(
            entries["Host"].get().strip(),
            entries["Porta"].get().strip(),
            entries["Usuário"].get().strip(),
            entries["Senha"].get(),
            entries["Database"].get().strip(),
        )
        try:
            cur = con.cursor()
            cur.execute("SELECT CGC FROM PESSOA WHERE CODPESSOA = ?", (int(cod),))
            row = cur.fetchone()
            return row[0] if row else ""
        finally:
            con.close()

    _requisicoes_recentes = deque(maxlen=3)  # Últimas 3 requisições
    _MIN_INTERVALO = 20  # 20 segundos

    def _pode_fazer_requisicao():
        agora = time.time()
        if len(_requisicoes_recentes) < 3:
            return True
        # Verificar se passaram 60 segundos desde a primeira das últimas 3
        return (agora - _requisicoes_recentes[0]) >= 60

    def _registrar_requisicao():
        _requisicoes_recentes.append(time.time())

    def atualizar_cnpj_api(cod=None):
        cod = (str(cod).strip() if cod is not None else edit_vars["CODPESSOA"].get().strip())
        if not cod:
            messagebox.showwarning("Atenção", "Selecione um registro.")
            return

        if cod and cod != edit_vars.get("CODPESSOA", tk.StringVar()).get().strip():
            cgc = _buscar_cgc_por_cod(cod)
        else:
            cgc = edit_vars.get("CGC").get().strip() if "CGC" in edit_vars else ""

        if not cgc:
            messagebox.showwarning("Atenção", "CNPJ não encontrado no cadastro selecionado.")
            return

        cnpj = _somente_digitos(cgc)
        if len(cnpj) != 14:
            messagebox.showwarning("Atenção", "CNPJ inválido.")
            return

        if not _pode_fazer_requisicao():
            aguardar = 60 - (time.time() - _requisicoes_recentes[0])
            messagebox.showwarning(
                "Aguarde", 
                f"Limite de 3 requisições por minuto.\nAguarde {int(aguardar)} segundos."
            )
            return
        
        _registrar_requisicao()
        try:
            if cnpj in _cache_cnpj:
                cache_data = _cache_cnpj[cnpj]
                if time.time() - cache_data['timestamp'] < 2592000:
                    data = cache_data['data']
                    messagebox.showinfo("Info", "Dados recuperados do cache local.")
                else:
                    raise KeyError("Cache expirado")
            else:
                raise KeyError("Não está em cache")
        except KeyError:
            try:
                # Substituir URL fixa por template configurável
                url = _build_api_url(api_url_var.get(), cnpj)
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Mozilla/5.0')
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                _cache_cnpj[cnpj] = {
                    'timestamp': time.time(),
                    'data': data
                }
                _salvar_cache()
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    messagebox.showerror("Limite Atingido", "Muitas requisições. Aguarde alguns minutos e tente novamente.")
                else:
                    messagebox.showerror("Erro HTTP", f"Erro {e.code}: {e.reason}")
                status_var.set(f"Falha ao consultar API CNPJ: HTTP {e.code}")
                return
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao consultar API CNPJ:\n{str(e)}")
                status_var.set(f"Falha ao consultar API CNPJ: {e}")
                return

        # === Extrair TODOS os dados da BrasilAPI ===
        nome = data.get("razao_social", "")
        fantasia = data.get("nome_fantasia", "")
        
        # Estabelecimento
        estabelecimento = data.get("estabelecimento", {})
        if not fantasia:
            fantasia = estabelecimento.get("nome_fantasia", "")
        
        # Email
        email = estabelecimento.get("email", "")
        
        # Telefones
        ddd1 = estabelecimento.get("ddd1", "")
        tel1 = estabelecimento.get("telefone1", "")
        ddd2 = estabelecimento.get("ddd2", "")
        tel2 = estabelecimento.get("telefone2", "")
        
        fone1 = f"{ddd1}{tel1}".replace(" ", "").replace("-", "").replace("(", "").replace(")", "") if ddd1 or tel1 else ""
        fone2 = f"{ddd2}{tel2}".replace(" ", "").replace("-", "").replace("(", "").replace(")", "") if ddd2 or tel2 else ""
        
        # Endereço completo
        tipo_logradouro = estabelecimento.get("tipo_logradouro", "")
        logradouro = estabelecimento.get("logradouro", "")
        numero = estabelecimento.get("numero", "")
        complemento = estabelecimento.get("complemento", "")
        bairro = estabelecimento.get("bairro", "")
        
        # Cidade/Estado
        cidade = estabelecimento.get("cidade", {})
        municipio = cidade.get("nome", "") if isinstance(cidade, dict) else ""
        cod_municipio = cidade.get("ibge_id", "") if isinstance(cidade, dict) else ""
        
        estado = estabelecimento.get("estado", {})
        uf = estado.get("sigla", "") if isinstance(estado, dict) else ""
        
        # CEP
        cep = (estabelecimento.get("cep", "") or "").replace(".", "").replace("-", "")
        
        # Montar endereço completo
        nome_rua = f"{tipo_logradouro} {logradouro}".strip() if tipo_logradouro else logradouro
        if numero:
            nome_rua = f"{nome_rua}, {numero}" if nome_rua else numero
        
        # Dados adicionais
        situacao_cadastral = data.get("descricao_situacao_cadastral", "")
        data_situacao = data.get("data_situacao_cadastral", "")
        natureza_juridica = data.get("natureza_juridica", "")
        porte = data.get("porte", "")
        data_abertura = data.get("data_inicio_atividade", "")
        cnae_fiscal = str(data.get("cnae_fiscal", ""))
        cnae_fiscal_descricao = data.get("cnae_fiscal_descricao", "")

        con = get_connection(
            entries["Host"].get().strip(),
            entries["Porta"].get().strip(),
            entries["Usuário"].get().strip(),
            entries["Senha"].get(),
            entries["Database"].get().strip(),
        )
        try:
            cur = con.cursor()
            
            # Verificar tamanho máximo dos campos
            def verificar_tamanho_campo(nome_campo):
                try:
                    cur.execute(f"""
                        SELECT f.RDB$FIELD_LENGTH
                        FROM RDB$RELATION_FIELDS rf
                        JOIN RDB$FIELDS f ON rf.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
                        WHERE rf.RDB$RELATION_NAME = 'PESSOA' 
                        AND rf.RDB$FIELD_NAME = '{nome_campo}'
                    """)
                    resultado = cur.fetchone()
                    return resultado[0] if resultado else None
                except:
                    return None
            
            # Limitar tamanhos dos campos
            tamanho_nome = verificar_tamanho_campo('NOME') or 100
            tamanho_fantasia = verificar_tamanho_campo('NOMEFANTASIA') or 100
            tamanho_email = verificar_tamanho_campo('EMAIL') or 100
            tamanho_rua = verificar_tamanho_campo('NOME_RUA') or 100
            tamanho_complemento = verificar_tamanho_campo('COMPLEMENTO') or 50
            tamanho_bairro = verificar_tamanho_campo('BAIRRO') or 50
            
            nome = nome[:tamanho_nome] if nome else ""
            fantasia = fantasia[:tamanho_fantasia] if fantasia else ""
            email = email[:tamanho_email] if email else ""
            nome_rua = nome_rua[:tamanho_rua] if nome_rua else ""
            complemento = complemento[:tamanho_complemento] if complemento else ""
            bairro = bairro[:tamanho_bairro] if bairro else ""
            
            # Verificar campos disponíveis
            cur.execute("SELECT FIRST 1 RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME='PESSOA' AND RDB$FIELD_NAME='ATUALIZADO_API'")
            tem_campo_api = cur.fetchone() is not None
            
            cur.execute("SELECT FIRST 1 RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME='PESSOA' AND RDB$FIELD_NAME='FONE2'")
            tem_fone2 = cur.fetchone() is not None
            
            # Campos básicos obrigatórios
            campos_update = [
                ("NOME", nome),
                ("NOMEFANTASIA", fantasia),
                ("EMAIL", email),
                ("FONE1", fone1),
                ("NOME_RUA", nome_rua),
                ("RUA_NUMERO", numero),
                ("COMPLEMENTO", complemento),
                ("BAIRRO", bairro),
                ("CEP", cep),
            ]
            
            # Adicionar FONE2 se existir
            if tem_fone2 and fone2:
                campos_update.append(("FONE2", fone2))
            
            # Adicionar flag API se existir
            if tem_campo_api:
                campos_update.append(("ATUALIZADO_API", "S"))
            
            # Verificar e adicionar campos opcionais
            campos_opcionais = [
                ("MUNICIPIO", municipio),
                ("UF", uf),
                ("COD_MUNICIPIO", cod_municipio),
                ("SITUACAO_CADASTRAL", situacao_cadastral),
                ("DATA_SITUACAO", data_situacao),
                ("NATUREZA_JURIDICA", natureza_juridica),
                ("PORTE", porte),
                ("DATA_ABERTURA", data_abertura),
                ("CNAE_FISCAL", cnae_fiscal),
                ("CNAE_DESCRICAO", cnae_fiscal_descricao),
            ]
            
            for campo, valor in campos_opcionais:
                if valor:
                    cur.execute(f"SELECT FIRST 1 RDB$FIELD_NAME FROM RDB$RELATION_FIELDS WHERE RDB$RELATION_NAME='PESSOA' AND RDB$FIELD_NAME='{campo}'")
                    if cur.fetchone():
                        campos_update.append((campo, valor))
            
            # Construir e executar SQL
            set_clause = ", ".join([f"{campo}=COALESCE(?, {campo})" for campo, _ in campos_update])
            valores = [valor for _, valor in campos_update]
            valores.append(int(cod))
            
            sql = f"UPDATE PESSOA SET {set_clause} WHERE CODPESSOA=?"
            cur.execute(sql, valores)
            con.commit()
        finally:
            con.close()

        on_load()
        
        # Mensagem detalhada de sucesso
        info_msg = "✅ Cadastro atualizado via API BrasilAPI\n\n"
        info_msg += "📋 DADOS CADASTRAIS\n"
        info_msg += f"Razão Social: {nome or 'N/A'}\n"
        info_msg += f"Nome Fantasia: {fantasia or 'N/A'}\n"
        if situacao_cadastral:
            info_msg += f"Situação: {situacao_cadastral}\n"
        if cnae_fiscal:
            info_msg += f"CNAE: {cnae_fiscal}"
            if cnae_fiscal_descricao:
                info_msg += f" - {cnae_fiscal_descricao}"
            info_msg += "\n"
        
        info_msg += "\n📍 ENDEREÇO\n"
        info_msg += f"{nome_rua or 'N/A'}\n"
        if bairro:
            info_msg += f"Bairro: {bairro}\n"
        info_msg += f"Cidade/UF: {municipio or 'N/A'}/{uf or 'N/A'}\n"
        if cep:
            info_msg += f"CEP: {cep}\n"
        
        info_msg += "\n📞 CONTATO\n"
        if fone1:
            info_msg += f"Telefone 1: {fone1}\n"
        if fone2:
            info_msg += f"Telefone 2: {fone2}\n"
        if email:
            info_msg += f"Email: {email}"
        else:
            info_msg += "Email: N/A"
        
        messagebox.showinfo("Sucesso", info_msg)
        status_var.set("✅ Cadastro atualizado via API com dados completos.")

    ttk.Button(edit_frame, text="Atualizar CNPJ (API)", command=atualizar_cnpj_api).grid(
        row=4, column=0, columnspan=4, pady=4
    )

    def on_load():
        try:
            con = get_connection(
                entries["Host"].get().strip(),
                entries["Porta"].get().strip(),
                entries["Usuário"].get().strip(),
                entries["Senha"].get(),
                entries["Database"].get().strip(),
            )
            try:
                columns, rows = fetch_people(con, filtro_var.get().strip())
            finally:
                con.close()

            tree.delete(*tree.get_children())
            tree["columns"] = columns
            for col in columns:
                width = 220 if col in ("ROYALTIES_DESCRICAO", "NOME", "NOMEFANTASIA") else 120
                tree.heading(col, text=col)
                tree.column(col, width=width, minwidth=80, stretch=True)

            idx_desc = columns.index("ROYALTIES_DESCRICAO") if "ROYALTIES_DESCRICAO" in columns else None
            for row in rows:
                if idx_desc is not None and (row[idx_desc] is None or str(row[idx_desc]).strip() == ""):
                    row = list(row)
                    row[idx_desc] = "Sem descrição"
                    row = tuple(row)
                tree.insert("", "end", values=row)

            status_var.set(f"Carregadas {len(rows)} pessoas.")
        except Exception as e:
            status_var.set(f"Falha ao carregar: {e}")

    ttk.Button(filtro_frame, text="Carregar/Filtrar", command=on_load).grid(
        row=0, column=3, padx=4
    )

    tree.bind("<<TreeviewSelect>>", carregar_selecao)

    # Atualização em massa
    massa_tab.columnconfigure(0, weight=1)
    massa_tab.rowconfigure(1, weight=1)

    ttk.Label(massa_tab, text="SQL de atualização em massa:").grid(
        row=0, column=0, sticky="w", padx=8, pady=4
    )
    sql_text = tk.Text(massa_tab, height=8)
    sql_text.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)

    def executar_sql_massa():
        sql = sql_text.get("1.0", tk.END).strip()
        if not sql:
            messagebox.showwarning("Atenção", "Informe o SQL.")
            return
        if not messagebox.askyesno("Confirmação", "Deseja executar o SQL informado?"):
            return
        try:
            con = get_connection(
                entries["Host"].get().strip(),
                entries["Porta"].get().strip(),
                entries["Usuário"].get().strip(),
                entries["Senha"].get(),
                entries["Database"].get().strip(),
            )
            try:
                cur = con.cursor()
                cur.execute(sql)
                con.commit()
            finally:
                con.close()
            status_var.set("SQL executado com sucesso.")
            on_load()
        except Exception as e:
            status_var.set(f"Falha ao executar SQL: {e}")

    ttk.Button(massa_tab, text="Executar SQL", command=executar_sql_massa).grid(
        row=2, column=0, pady=8
    )

    # Aba Problemas
    problemas_tab.columnconfigure(0, weight=1)
    problemas_tab.rowconfigure(1, weight=1)

    ttk.Label(problemas_tab, text="Lista de problemas nos cadastros:").grid(
        row=0, column=0, sticky="w", padx=8, pady=4
    )

    problemas_frame = ttk.Frame(problemas_tab)
    problemas_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)

    problemas_tree = ttk.Treeview(problemas_frame, show="headings")
    p_vsb = ttk.Scrollbar(problemas_frame, orient="vertical", command=problemas_tree.yview)
    p_hsb = ttk.Scrollbar(problemas_frame, orient="horizontal", command=problemas_tree.xview)
    problemas_tree.configure(yscrollcommand=p_vsb.set, xscrollcommand=p_hsb.set)

    problemas_tree.grid(row=0, column=0, sticky="nsew")
    p_vsb.grid(row=0, column=1, sticky="ns")
    p_hsb.grid(row=1, column=0, sticky="ew")

    problemas_frame.columnconfigure(0, weight=1)
    problemas_frame.rowconfigure(0, weight=1)

    def carregar_problemas():
        try:
            con = get_connection(
                entries["Host"].get().strip(),
                entries["Porta"].get().strip(),
                entries["Usuário"].get().strip(),
                entries["Senha"].get(),
                entries["Database"].get().strip(),
            )
            try:
                columns, rows = fetch_people(con, "")
            finally:
                con.close()

            problemas = analisar_problemas(columns, rows)
            problemas_tree.delete(*problemas_tree.get_children())
            problemas_tree["columns"] = ["CODPESSOA", "NOME", "TIPO", "CPF_CNPJ", "ERRO"]
            for col in problemas_tree["columns"]:
                width = 240 if col in ("NOME", "ERRO") else 140
                problemas_tree.heading(col, text=col)
                problemas_tree.column(col, width=width, minwidth=80, stretch=True)

            for item in problemas:
                problemas_tree.insert("", "end", values=item)

            status_var.set(f"Encontrados {len(problemas)} problemas.")
        except Exception as e:
            status_var.set(f"Falha ao analisar: {e}")

    ttk.Button(problemas_tab, text="Analisar cadastros", command=carregar_problemas).grid(
        row=2, column=0, pady=8, padx=8, sticky="w"
    )

    def abrir_ajuste_massa():
        try:
            con = get_connection(
                entries["Host"].get().strip(),
                entries["Porta"].get().strip(),
                entries["Usuário"].get().strip(),
                entries["Senha"].get(),
                entries["Database"].get().strip(),
            )
            try:
                columns, rows = fetch_people(con, "")
            finally:
                con.close()

            sugestoes = sugerir_ajustes_massa(columns, rows)
            if not sugestoes:
                messagebox.showinfo("Ajuste em massa (IA)", "Nenhuma sugestão encontrada.")
                return

            top = tk.Toplevel(root)
            top.title("Ajuste em massa (IA) - Prévia")
            top.geometry("900x500")

            frame = ttk.Frame(top)
            frame.pack(fill="both", expand=True, padx=8, pady=8)

            tree_adj = ttk.Treeview(frame, show="headings")
            vsb = ttk.Scrollbar(frame, orient="vertical", command=tree_adj.yview)
            hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree_adj.xview)
            tree_adj.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

            tree_adj["columns"] = ["CODPESSOA", "CAMPO", "VALOR_NOVO", "MOTIVO"]
            for col in tree_adj["columns"]:
                width = 320 if col in ("VALOR_NOVO", "MOTIVO") else 140
                tree_adj.heading(col, text=col)
                tree_adj.column(col, width=width, minwidth=80, stretch=True)

            for cod, campo, valor, motivo in sugestoes:
                tree_adj.insert("", "end", values=(cod, campo, valor if valor is not None else "", motivo))

            tree_adj.grid(row=0, column=0, sticky="nsew")
            vsb.grid(row=0, column=1, sticky="ns")
            hsb.grid(row=1, column=0, sticky="ew")

            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(0, weight=1)

            def aplicar_ajustes():
                if not messagebox.askyesno("Confirmação", "Deseja aplicar os ajustes sugeridos?"):
                    return
                try:
                    con = get_connection(
                        entries["Host"].get().strip(),
                        entries["Porta"].get().strip(),
                        entries["Usuário"].get().strip(),
                        entries["Senha"].get(),
                        entries["Database"].get().strip(),
                    )
                    try:
                        cur = con.cursor()
                        por_cadastro = {}
                        for cod, campo, valor, _ in sugestoes:
                            por_cadastro.setdefault(cod, {})[campo] = valor

                        for cod, campos in por_cadastro.items():
                            cols = list(campos.keys())
                            vals = [campos[c] for c in cols]
                            sql = "UPDATE PESSOA SET " + ", ".join([f"{c}=?" for c in cols]) + " WHERE CODPESSOA=?"
                            cur.execute(sql, (*vals, int(cod)))

                        con.commit()
                    finally:
                        con.close()

                    on_load()
                    status_var.set(f"Ajustes aplicados: {len(sugestoes)}.")
                    top.destroy()
                except Exception as e:
                    status_var.set(f"Falha ao aplicar ajustes: {e}")

            ttk.Button(top, text="Aplicar ajustes (IA)", command=aplicar_ajustes).pack(
                anchor="e", padx=8, pady=6
            )
        except Exception as e:
            status_var.set(f"Falha no ajuste em massa: {e}")

    def _atualizar_cnpj_api_problemas():
        sel = problemas_tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um cadastro na lista de problemas.")
            return
        cod = problemas_tree.item(sel[0], "values")[0]
        atualizar_cnpj_api(cod)

    ttk.Button(problemas_tab, text="Ajuste em massa (IA)", command=abrir_ajuste_massa).grid(
        row=2, column=0, pady=8, padx=220, sticky="w"
    )
    ttk.Button(problemas_tab, text="Atualizar CNPJ (API)", command=_atualizar_cnpj_api_problemas).grid(
        row=2, column=0, pady=8, padx=420, sticky="w"
    )

    # --- Nova aba: Atualizar via API ---
    api_tab.columnconfigure(0, weight=1)
    api_tab.rowconfigure(2, weight=1)

    ttk.Label(api_tab, text="URL da API (use {cnpj}):").grid(
        row=0, column=0, sticky="w", padx=8, pady=4
    )
    ttk.Entry(api_tab, textvariable=api_url_var, width=80).grid(
        row=0, column=0, sticky="e", padx=8, pady=4
    )

    api_frame = ttk.Frame(api_tab)
    api_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
    api_frame.columnconfigure(0, weight=1)
    api_frame.rowconfigure(0, weight=1)

    api_tree = ttk.Treeview(api_frame, show="headings", selectmode="browse")
    api_vsb = ttk.Scrollbar(api_frame, orient="vertical", command=api_tree.yview)
    api_hsb = ttk.Scrollbar(api_frame, orient="horizontal", command=api_tree.xview)
    api_tree.configure(yscrollcommand=api_vsb.set, xscrollcommand=api_hsb.set)

    api_tree.grid(row=0, column=0, sticky="nsew")
    api_vsb.grid(row=0, column=1, sticky="ns")
    api_hsb.grid(row=1, column=0, sticky="ew")

    def carregar_cnpjs_validos():
        try:
            con = get_connection(
                entries["Host"].get().strip(),
                entries["Porta"].get().strip(),
                entries["Usuário"].get().strip(),
                entries["Senha"].get(),
                entries["Database"].get().strip(),
            )
            try:
                columns, rows = fetch_people(con, "")
            finally:
                con.close()

            # Filtrar apenas cadastros com CNPJ válido
            idx = {c: i for i, c in enumerate(columns)}
            cnpj_idx = idx.get("CGC")
            cod_idx = idx.get("CODPESSOA")
            nome_idx = idx.get("NOME")
            fantasia_idx = idx.get("NOMEFANTASIA")
            email_idx = idx.get("EMAIL")
            fone_idx = idx.get("FONE1")

            validos = []
            for row in rows:
                cnpj = row[cnpj_idx] if cnpj_idx is not None else ""
                if cnpj and validar_cnpj(cnpj):
                    validos.append(row)

            # Exibir na treeview
            api_tree.delete(*api_tree.get_children())
            exibe_cols = ["CODPESSOA", "NOME", "CGC", "NOMEFANTASIA", "EMAIL", "FONE1"]
            api_tree["columns"] = exibe_cols
            for col in exibe_cols:
                width = 220 if col in ("NOME", "NOMEFANTASIA") else 120
                api_tree.heading(col, text=col)
                api_tree.column(col, width=width, minwidth=80, stretch=True)

            for row in validos:
                api_tree.insert(
                    "", "end",
                    values=(
                        row[cod_idx] if cod_idx is not None else "",
                        row[nome_idx] if nome_idx is not None else "",
                        row[cnpj_idx] if cnpj_idx is not None else "",
                        row[fantasia_idx] if fantasia_idx is not None else "",
                        row[email_idx] if email_idx is not None else "",
                        row[fone_idx] if fone_idx is not None else "",
                    )
                )
            status_var.set(f"Listados {len(validos)} cadastros com CNPJ válido.")
        except Exception as e:
            status_var.set(f"Falha ao carregar CNPJs válidos: {e}")

    def atualizar_selecionado_api():
        sel = api_tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um cadastro para atualizar via API.")
            return
        cod = api_tree.item(sel[0], "values")[0]
        atualizar_cnpj_api(cod)
        carregar_cnpjs_validos()  # Atualiza a lista após atualização

    ttk.Button(api_tab, text="Carregar lista", command=carregar_cnpjs_validos).grid(
        row=2, column=0, sticky="w", padx=8, pady=4
    )
    ttk.Button(api_tab, text="Atualizar selecionado via API", command=atualizar_selecionado_api).grid(
        row=2, column=0, sticky="e", padx=8, pady=4
    )

    # Ajuste para garantir que a aba "Atualizar via API" carregue a lista ao ser selecionada
    def on_tab_changed(event):
        tab = event.widget.tab(event.widget.index("current"))["text"]
        if tab == "Atualizar via API":
            carregar_cnpjs_validos()
    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

    # === ABA DE VALIDAÇÃO ===
    validacao_tab.columnconfigure(0, weight=1)
    validacao_tab.rowconfigure(1, weight=1)

    ttk.Label(validacao_tab, text="Validação de Documentos", font=("Segoe UI", 12, "bold")).grid(
        row=0, column=0, sticky="w", padx=8, pady=8
    )

    val_frame = ttk.Frame(validacao_tab)
    val_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
    val_frame.columnconfigure(0, weight=1)
    val_frame.rowconfigure(0, weight=1)

    val_tree = ttk.Treeview(val_frame, show="headings")
    val_vsb = ttk.Scrollbar(val_frame, orient="vertical", command=val_tree.yview)
    val_hsb = ttk.Scrollbar(val_frame, orient="horizontal", command=val_tree.xview)
    val_tree.configure(yscrollcommand=val_vsb.set, xscrollcommand=val_hsb.set)

    val_tree.grid(row=0, column=0, sticky="nsew")
    val_vsb.grid(row=0, column=1, sticky="ns")
    val_hsb.grid(row=1, column=0, sticky="ew")

    def carregar_validacao():
        try:
            con = get_connection(
                entries["Host"].get().strip(),
                entries["Porta"].get().strip(),
                entries["Usuário"].get().strip(),
                entries["Senha"].get(),
                entries["Database"].get().strip(),
            )
            try:
                columns, rows = fetch_people(con, "")
            finally:
                con.close()

            idx = {c: i for i, c in enumerate(columns)}
            validacoes = []
            
            for row in rows:
                cod = row[idx["CODPESSOA"]] if "CODPESSOA" in idx else ""
                nome = row[idx["NOME"]] if "NOME" in idx else ""
                tipo = (row[idx["TIPO"]] if "TIPO" in idx else "").strip().upper()
                cpf = row[idx["CPF"]] if "CPF" in idx else ""
                cnpj = row[idx["CGC"]] if "CGC" in idx else ""
                
                status_cpf = "✅ Válido" if cpf and validar_cpf(cpf) else ("❌ Inválido" if cpf else "⚪ Não informado")
                status_cnpj = "✅ Válido" if cnpj and validar_cnpj(cnpj) else ("❌ Inválido" if cnpj else "⚪ Não informado")
                
                validacoes.append((cod, nome, tipo, cpf or "-", status_cpf, cnpj or "-", status_cnpj))

            val_tree.delete(*val_tree.get_children())
            val_tree["columns"] = ["COD", "NOME", "TIPO", "CPF", "STATUS_CPF", "CNPJ", "STATUS_CNPJ"]
            
            for col in val_tree["columns"]:
                width = 250 if col == "NOME" else 120
                val_tree.heading(col, text=col)
                val_tree.column(col, width=width, minwidth=80, stretch=True)

            for item in validacoes:
                val_tree.insert("", "end", values=item)

            status_var.set(f"Validados {len(validacoes)} cadastros.")
        except Exception as e:
            status_var.set(f"Falha ao validar: {e}")

    ttk.Button(validacao_tab, text="🔍 Validar Documentos", command=carregar_validacao).grid(
        row=2, column=0, pady=8
    )

    # === ABA DE DUPLICADOS ===
    duplicados_tab.columnconfigure(0, weight=1)
    duplicados_tab.rowconfigure(1, weight=1)

    ttk.Label(duplicados_tab, text="Cadastros Duplicados", font=("Segoe UI", 12, "bold")).grid(
        row=0, column=0, sticky="w", padx=8, pady=8
    )

    dup_notebook = ttk.Notebook(duplicados_tab)
    dup_notebook.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)

    # Sub-aba CPF duplicado
    dup_cpf_frame = ttk.Frame(dup_notebook)
    dup_notebook.add(dup_cpf_frame, text="CPF Duplicados")
    
    dup_cpf_frame.columnconfigure(0, weight=1)
    dup_cpf_frame.rowconfigure(0, weight=1)

    dup_cpf_tree = ttk.Treeview(dup_cpf_frame, show="headings")
    cpf_vsb = ttk.Scrollbar(dup_cpf_frame, orient="vertical", command=dup_cpf_tree.yview)
    cpf_hsb = ttk.Scrollbar(dup_cpf_frame, orient="horizontal", command=dup_cpf_tree.xview)
    dup_cpf_tree.configure(yscrollcommand=cpf_vsb.set, xscrollcommand=cpf_hsb.set)

    dup_cpf_tree.grid(row=0, column=0, sticky="nsew")
    cpf_vsb.grid(row=0, column=1, sticky="ns")
    cpf_hsb.grid(row=1, column=0, sticky="ew")

    # Sub-aba CNPJ duplicado
    dup_cnpj_frame = ttk.Frame(dup_notebook)
    dup_notebook.add(dup_cnpj_frame, text="CNPJ Duplicados")
    
    dup_cnpj_frame.columnconfigure(0, weight=1)
    dup_cnpj_frame.rowconfigure(0, weight=1)

    dup_cnpj_tree = ttk.Treeview(dup_cnpj_frame, show="headings")
    cnpj_vsb = ttk.Scrollbar(dup_cnpj_frame, orient="vertical", command=dup_cnpj_tree.yview)
    cnpj_hsb = ttk.Scrollbar(dup_cnpj_frame, orient="horizontal", command=dup_cnpj_tree.xview)
    dup_cnpj_tree.configure(yscrollcommand=cnpj_vsb.set, xscrollcommand=cnpj_hsb.set)

    dup_cnpj_tree.grid(row=0, column=0, sticky="nsew")
    cnpj_vsb.grid(row=0, column=1, sticky="ns")
    cnpj_hsb.grid(row=1, column=0, sticky="ew")

    def carregar_duplicados():
        try:
            con = get_connection(
                entries["Host"].get().strip(),
                entries["Porta"].get().strip(),
                entries["Usuário"].get().strip(),
                entries["Senha"].get(),
                entries["Database"].get().strip(),
            )
            try:
                columns, rows = fetch_people(con, "")
            finally:
                con.close()

            idx = {c: i for i, c in enumerate(columns)}
            cpfs = {}
            cnpjs = {}
            
            # Agrupar por documento
            for row in rows:
                cpf = _somente_digitos(row[idx["CPF"]] if "CPF" in idx else "")
                cnpj = _somente_digitos(row[idx["CGC"]] if "CGC" in idx else "")
                
                if cpf and len(cpf) == 11:
                    cpfs.setdefault(cpf, []).append(row)
                if cnpj and len(cnpj) == 14:
                    cnpjs.setdefault(cnpj, []).append(row)

            # CPF duplicados
            dup_cpf_tree.delete(*dup_cpf_tree.get_children())
            dup_cpf_tree["columns"] = ["CPF", "COD", "NOME", "EMAIL", "AÇÃO"]
            
            for col in dup_cpf_tree["columns"]:
                width = 200 if col in ("NOME", "EMAIL") else 120
                dup_cpf_tree.heading(col, text=col)
                dup_cpf_tree.column(col, width=width, minwidth=80, stretch=True)

            for cpf, registros in cpfs.items():
                if len(registros) > 1:
                    for row in registros:
                        dup_cpf_tree.insert("", "end", values=(
                            cpf,
                            row[idx["CODPESSOA"]] if "CODPESSOA" in idx else "",
                            row[idx["NOME"]] if "NOME" in idx else "",
                            row[idx["EMAIL"]] if "EMAIL" in idx else "",
                            "🔴 Duplicado"
                        ))

            # CNPJ duplicados
            dup_cnpj_tree.delete(*dup_cnpj_tree.get_children())
            dup_cnpj_tree["columns"] = ["CNPJ", "COD", "NOME", "EMAIL", "AÇÃO"]
            
            for col in dup_cnpj_tree["columns"]:
                width = 200 if col in ("NOME", "EMAIL") else 120
                dup_cnpj_tree.heading(col, text=col)
                dup_cnpj_tree.column(col, width=width, minwidth=80, stretch=True)

            for cnpj, registros in cnpjs.items():
                if len(registros) > 1:
                    for row in registros:
                        dup_cnpj_tree.insert("", "end", values=(
                            cnpj,
                            row[idx["CODPESSOA"]] if "CODPESSOA" in idx else "",
                            row[idx["NOME"]] if "NOME" in idx else "",
                            row[idx["EMAIL"]] if "EMAIL" in idx else "",
                            "🔴 Duplicado"
                        ))

            total_dup = sum(1 for v in cpfs.values() if len(v) > 1) + sum(1 for v in cnpjs.values() if len(v) > 1)
            status_var.set(f"Encontrados {total_dup} grupos de duplicados.")
        except Exception as e:
            status_var.set(f"Falha ao carregar duplicados: {e}")

    def inativar_duplicado_selecionado():
        # Determinar qual árvore está ativa
        current_tab = dup_notebook.index(dup_notebook.select())
        tree_atual = dup_cpf_tree if current_tab == 0 else dup_cnpj_tree
        
        sel = tree_atual.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um cadastro duplicado.")
            return
        
        cod = tree_atual.item(sel[0], "values")[1]
        
        if not messagebox.askyesno("Confirmação", f"Deseja inativar o cadastro {cod}?"):
            return
        
        try:
            con = get_connection(
                entries["Host"].get().strip(),
                entries["Porta"].get().strip(),
                entries["Usuário"].get().strip(),
                entries["Senha"].get(),
                entries["Database"].get().strip(),
            )
            try:
                cur = con.cursor()
                # Tentar diferentes campos de inativação
                try:
                    cur.execute("UPDATE PESSOA SET SITUACAO='I' WHERE CODPESSOA=?", (int(cod),))
                except:
                    cur.execute("UPDATE PESSOA SET CADASTRO_VALIDO='N' WHERE CODPESSOA=?", (int(cod),))
                con.commit()
            finally:
                con.close()
            
            carregar_duplicados()
            status_var.set(f"Cadastro {cod} inativado com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao inativar: {e}")

    btn_frame = ttk.Frame(duplicados_tab)
    btn_frame.grid(row=2, column=0, pady=8, sticky="ew", padx=8)
    
    ttk.Button(btn_frame, text="🔍 Buscar Duplicados", command=carregar_duplicados).pack(side="left", padx=4)
    ttk.Button(btn_frame, text="🔴 Inativar Selecionado", command=inativar_duplicado_selecionado).pack(side="left", padx=4)

    # === ABA DE RELATÓRIOS ===
    relatorios_tab.columnconfigure(0, weight=1)
    relatorios_tab.rowconfigure(0, weight=1)

    rel_text = tk.Text(relatorios_tab, wrap="word", font=("Consolas", 10))
    rel_text.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
    
    rel_scroll = ttk.Scrollbar(relatorios_tab, orient="vertical", command=rel_text.yview)
    rel_scroll.grid(row=0, column=1, sticky="ns")
    rel_text.configure(yscrollcommand=rel_scroll.set)

    def gerar_relatorio():
        try:
            con = get_connection(
                entries["Host"].get().strip(),
                entries["Porta"].get().strip(),
                entries["Usuário"].get().strip(),
                entries["Senha"].get(),
                entries["Database"].get().strip(),
            )
            try:
                columns, rows = fetch_people(con, "")
            finally:
                con.close()

            idx = {c: i for i, c in enumerate(columns)}
            
            total = len(rows)
            tipo_f = sum(1 for r in rows if (r[idx["TIPO"]] if "TIPO" in idx else "").strip().upper() == "F")
            tipo_j = sum(1 for r in rows if (r[idx["TIPO"]] if "TIPO" in idx else "").strip().upper() == "J")
            
            cpf_validos = sum(1 for r in rows if validar_cpf(r[idx["CPF"]] if "CPF" in idx else ""))
            cnpj_validos = sum(1 for r in rows if validar_cnpj(r[idx["CGC"]] if "CGC" in idx else ""))
            
            sem_email = sum(1 for r in rows if not (r[idx["EMAIL"]] if "EMAIL" in idx else ""))
            sem_telefone = sum(1 for r in rows if not (r[idx["FONE1"]] if "FONE1" in idx else ""))
            
            rel_text.delete("1.0", tk.END)
            rel_text.insert("1.0", f"""
╔══════════════════════════════════════════════════════════╗
║         RELATÓRIO GERAL DE CADASTROS                     ║
╚══════════════════════════════════════════════════════════╝

📊 ESTATÍSTICAS GERAIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total de cadastros:              {total:>10}
Pessoa Física (F):               {tipo_f:>10}
Pessoa Jurídica (J):             {tipo_j:>10}

📋 VALIDAÇÃO DE DOCUMENTOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CPF válidos:                     {cpf_validos:>10}
CNPJ válidos:                    {cnpj_validos:>10}

📞 INFORMAÇÕES DE CONTATO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sem e-mail:                      {sem_email:>10}
Sem telefone:                    {sem_telefone:>10}

✅ QUALIDADE DOS DADOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Taxa de CPF válidos:             {(cpf_validos/max(tipo_f,1)*100):>9.1f}%
Taxa de CNPJ válidos:            {(cnpj_validos/max(tipo_j,1)*100):>9.1f}%
Taxa de cadastros com e-mail:    {((total-sem_email)/max(total,1)*100):>9.1f}%
Taxa de cadastros com telefone:  {((total-sem_telefone)/max(total,1)*100):>9.1f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Relatório gerado em: {time.strftime('%d/%m/%Y %H:%M:%S')}
""")
            status_var.set("Relatório gerado com sucesso.")
        except Exception as e:
            rel_text.insert("1.0", f"Erro ao gerar relatório: {e}")

    ttk.Button(relatorios_tab, text="📊 Gerar Relatório", command=gerar_relatorio).grid(
        row=1, column=0, columnspan=2, pady=8
    )

    # Ajuste para garantir que as abas carreguem automaticamente ao serem selecionadas
    def on_tab_changed(event):
        tab = event.widget.tab(event.widget.index("current"))["text"]
        if tab == "🌐 Atualizar via API":
            carregar_cnpjs_validos()
        elif tab == "✅ Validação":
            carregar_validacao()
        elif tab == "👥 Duplicados":
            carregar_duplicados()
        elif tab == "📊 Relatórios":
            gerar_relatorio()
    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

    # Melhorar estilo visual
    style.configure("TNotebook.Tab", padding=[20, 10], font=("Segoe UI", 10))
    style.configure("TButton", padding=[10, 5], font=("Segoe UI", 9))
    style.configure("TLabel", font=("Segoe UI", 9))
    
    root.rowconfigure(len(fields) + 1, weight=1)
    root.mainloop()

# URL template da API (permite trocar por outra API)
API_URL_TEMPLATE = os.getenv("CNPJ_API_URL_TEMPLATE", "https://brasilapi.com.br/api/cnpj/v1/{cnpj}")

def _build_api_url(template, cnpj):
    tpl = (template or "").strip()
    if "{cnpj}" in tpl:
        return tpl.format(cnpj=cnpj)
    return tpl.rstrip("/") + f"/{cnpj}"

if __name__ == "__main__":
    launch_gui()