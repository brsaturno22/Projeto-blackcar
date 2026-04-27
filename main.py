import os, sqlite3, webbrowser, urllib.parse, random, string
import flet as ft
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURAÇÃO ---
DB_PATH = "black_car_service.db"
PASTA_RECIBOS = os.path.abspath("comprovantes")
if not os.path.exists(PASTA_RECIBOS):
    os.makedirs(PASTA_RECIBOS)

def executar_query(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if fetch: return cursor.fetchall()
        conn.commit()
    finally: conn.close()

# Inicialização de Tabelas
executar_query("CREATE TABLE IF NOT EXISTS base_clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, veiculo TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS servicos (cliente TEXT, veiculo TEXT, servico TEXT, valor REAL, data TEXT, id_rastreio TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS agendamentos (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, data TEXT, status TEXT)")

# Catálogo e Serviços Preservados
catalogo = {
    "Toyota": ["Corolla", "Hilux", "SW4", "Etios", "Yaris", "RAV4", "Camry"],
    "VW": ["Gol", "Polo", "Jetta", "Nivus", "T-Cross", "Virtus", "Amarok", "Saveiro", "Golf", "Voyage"],
    "Chevrolet": ["Onix", "S10", "Cruze", "Tracker", "Spin", "Equinox", "Montana", "Prisma", "Celta", "Astra"],
    "Fiat": ["Strada", "Toro", "Argo", "Mobi", "Cronos", "Pulse", "Fastback", "Uno", "Palio", "Siena", "Fiorino"],
    "Honda": ["Civic", "HR-V", "Fit", "City", "CR-V", "WR-V"],
    "Hyundai": ["HB20", "HB20S", "Creta", "Tucson", "Santa Fe", "i30", "Ix35"],
    "Jeep": ["Renegade", "Compass", "Commander", "Grand Cherokee"],
    "Renault": ["Sandero", "Duster", "Kwid", "Logan", "Oroch", "Captur", "Master"],
    "Ford": ["Ka", "EcoSport", "Ranger", "Fiesta", "Focus", "Fusion", "Territory"],
    "Nissan": ["Kicks", "Frontier", "Versa", "March", "Sentra"],
    "Mitsubishi": ["L200 Triton", "ASX", "Pajero", "Outlander"]
}
servicos_lista = ["Troca de Óleo e Filtros", "Revisão Geral", "Sistema de Freios", "Suspensão", "Embreagem", "Correia Dentada", "Limpeza de Injeção", "Arrefecimento", "Câmbio", "Elétrica", "Ar Condicionado", "Alinhamento", "Escapamento", "Scanner Diagnóstico", "Polimento", "Motor"]

def main(page: ft.Page):
    page.title = "Black Car Service Pro"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#050505"
    page.padding = 10
    dados_temp = {"nome": ""}
    
    def mudar_tela(view):
        container_principal.content = view
        page.update()

    def gerar_id_rastreio():
        return "BCS-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    def processar_recibo(id_r, cliente, veiculo, servico, valor):
        img = Image.new('RGB', (600, 1100), color='#050505')
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 590, 1090], outline="#e63946", width=5)
        try:
            f_h = ImageFont.truetype("arial.ttf", 48); f_i = ImageFont.truetype("arial.ttf", 28); f_f = ImageFont.truetype("arial.ttf", 18)
        except: f_h = f_i = f_f = ImageFont.load_default()
        draw.text((300, 100), "BLACK CAR SERVICE", fill="#e63946", font=f_h, anchor="ms")
        draw.text((60, 220), f"O.S.: {id_r}", fill="#00ff41", font=f_i)
        draw.text((60, 320), f"CLIENTE: {cliente}", fill="white", font=f_i)
        draw.text((60, 420), f"VEICULO: {veiculo}", fill="white", font=f_i)
        draw.text((60, 520), f"SERVICO: {servico}", fill="white", font=f_i)
        draw.rectangle([50, 820, 550, 950], fill="#111", outline="#e63946")
        draw.text((300, 900), f"TOTAL: R$ {valor:.2f}", fill="#00ff41", font=f_h, anchor="ms")
        draw.text((300, 1020), "QUALIDADE • CONFIANÇA • PERFORMANCE", fill="#e63946", font=f_f, anchor="ms")
        img.save(os.path.join(PASTA_RECIBOS, f"Recibo_{id_r}.jpg"), "JPEG", quality=95)
        dlg = ft.AlertDialog(title=ft.Text("Recibo Criado!"), content=ft.Text(f"Salvo em: {PASTA_RECIBOS}"), actions=[ft.TextButton("OK", on_click=lambda _: (setattr(dlg, "open", False), page.update()))])
        page.dialog = dlg; dlg.open = True; page.update()

    def tela_home(): return ft.Column([ft.Container(height=60), ft.Text("🚗", size=80), ft.Text("BLACK CAR SERVICE", size=30, weight="bold", color="#e63946")], horizontal_alignment="center")

    def tela_clientes():
        col = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=480, spacing=4)
        def carregar(f=""):
            col.controls.clear()
            for r in executar_query("SELECT ROWID, nome, veiculo FROM base_clientes WHERE nome LIKE ?", (f"%{f}%",), fetch=True):
                col.controls.append(ft.Container(bgcolor="#111", border=ft.border.all(1, "#2196F3"), padding=6, border_radius=5, content=ft.Row([
                    ft.Column([ft.Text(r[1], size=13, weight="bold", color="#2196F3"), ft.Text(r[2], size=10)], expand=True),
                    ft.IconButton(ft.Icons.DELETE, icon_color="red", on_click=lambda e, cid=r[0]: (executar_query("DELETE FROM base_clientes WHERE ROWID=?", (cid,)), carregar()))
                ])))
            page.update()
        search = ft.TextField(label="Buscar cliente...", border_color="#2196F3", on_change=lambda e: carregar(e.control.value))
        carregar(); return ft.Column([ft.Row([ft.Text("CLIENTES", size=18, color="#2196F3"), ft.IconButton(ft.Icons.ADD, icon_color="#2196F3", on_click=lambda _: abrir_modal_cad())], alignment="spaceBetween"), search, col])

    def abrir_modal_cad():
        dlg = ft.AlertDialog(title=ft.Text("Novo Registro"))
        def p1():
            t = ft.TextField(label="Nome", capitalization=ft.TextCapitalization.CHARACTERS); dlg.content = t
            dlg.actions = [ft.TextButton("PRÓXIMO", on_click=lambda _: p2(t.value))]
            if dlg not in page.overlay: page.overlay.append(dlg)
            dlg.open = True; page.update()
        def p2(n):
            dados_temp["nome"] = n.upper(); m = ft.Dropdown(label="Marca", options=[ft.dropdown.Option(x) for x in sorted(catalogo.keys())])
            dlg.content = m; dlg.actions = [ft.TextButton("PRÓXIMO", on_click=lambda _: p3(m.value))]; page.update()
        def p3(mrc):
            md = ft.Dropdown(label="Modelo", options=[ft.dropdown.Option(x) for x in sorted(catalogo[mrc])])
            dlg.content = md; dlg.actions = [ft.TextButton("FINALIZAR", on_click=lambda _: (executar_query("INSERT INTO base_clientes (nome, veiculo) VALUES (?,?)", (dados_temp["nome"], f"{mrc} {md.value}")), setattr(dlg, "open", False), page.update(), mudar_tela(tela_clientes())))]; page.update()
        p1()

    def tela_checkin():
        res_c = executar_query("SELECT nome FROM base_clientes ORDER BY nome ASC", fetch=True)
        drop_cli = ft.Dropdown(label="Cliente", border_color="#e63946", options=[ft.dropdown.Option(r[0]) for r in res_c])
        drop_srv = ft.Dropdown(label="Serviço", border_color="#e63946", options=[ft.dropdown.Option(s) for s in servicos_lista])
        txt_val = ft.TextField(label="Valor", border_color="#e63946", prefix=ft.Text("R$ "), keyboard_type=ft.KeyboardType.NUMBER)
        def salvar(e, gerar):
            if not drop_cli.value: return
            id_r = gerar_id_rastreio(); val = float(txt_val.value.replace(",", ".") or 0)
            res_v = executar_query("SELECT veiculo FROM base_clientes WHERE nome=?", (drop_cli.value,), fetch=True)
            veic = res_v[0][0] if res_v else "Carro"
            executar_query("INSERT INTO servicos (cliente, veiculo, servico, valor, data, id_rastreio) VALUES (?,?,?,?,?,?)", (drop_cli.value, veic, drop_srv.value, val, datetime.now().strftime("%d/%m/%Y"), id_r))
            if gerar: processar_recibo(id_r, drop_cli.value, veic, drop_srv.value, val)
            mudar_tela(tela_home())
        return ft.Column([ft.Text("CHECK-IN", size=20, weight="bold", color="#e63946"), drop_cli, drop_srv, txt_val, ft.ElevatedButton("SALVAR", on_click=lambda e: salvar(e, False), width=400), ft.ElevatedButton("GERAR RECIBO", on_click=lambda e: salvar(e, True), width=400, bgcolor="#e63946", color="white")], scroll=ft.ScrollMode.ALWAYS)

    def tela_agenda():
        col_ag = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=350, spacing=4)
        def carregar_agenda():
            col_ag.controls.clear()
            for a in executar_query("SELECT ROWID, cliente, data FROM agendamentos WHERE status = 'ABERTO' ORDER BY data ASC", fetch=True):
                col_ag.controls.append(ft.Container(bgcolor="#111", border=ft.border.all(1, "#9C27B0"), padding=8, border_radius=5, content=ft.Row([
                    ft.Column([ft.Text(a[1], size=13, weight="bold", color="#9C27B0"), ft.Text(a[2], size=10)], expand=True),
                    ft.IconButton(ft.Icons.CHECK_CIRCLE, icon_color="#00ff41", on_click=lambda e, id_ag=a[0]: (executar_query("UPDATE agendamentos SET status='CONCLUIDO' WHERE ROWID=?", (id_ag,)), carregar_agenda())),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color="red", on_click=lambda e, id_ag=a[0]: (executar_query("DELETE FROM agendamentos WHERE ROWID=?", (id_ag,)), carregar_agenda()))
                ])))
            page.update()
        res_c = executar_query("SELECT nome FROM base_clientes ORDER BY nome ASC", fetch=True)
        drop_ag = ft.Dropdown(label="Cliente", border_color="#9C27B0", options=[ft.dropdown.Option(c[0]) for c in res_c])
        btn_d = ft.ElevatedButton("Data", icon=ft.Icons.CALENDAR_MONTH, color="#9C27B0", on_click=lambda _: (setattr(dp, "open", True), page.update()))
        dp = ft.DatePicker(on_change=lambda e: (setattr(btn_d, "text", e.control.value.strftime("%d/%m/%Y")), page.update()))
        def agendar(e):
            if drop_ag.value and btn_d.text != "Data":
                executar_query("INSERT INTO agendamentos (cliente, data, status) VALUES (?,?,?)", (drop_ag.value, btn_d.text, 'ABERTO'))
                carregar_agenda()
        page.overlay.append(dp); carregar_agenda()
        return ft.Column([ft.Text("AGENDA", size=20, weight="bold", color="#9C27B0"), drop_ag, btn_d, ft.ElevatedButton("AGENDAR", width=400, bgcolor="#9C27B0", color="white", on_click=agendar), ft.Divider(), col_ag])

    def tela_historico():
        lista = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=500, spacing=4)
        def carregar():
            lista.controls.clear()
            for s in executar_query("SELECT ROWID, cliente, servico, valor, data FROM servicos ORDER BY ROWID DESC", fetch=True):
                lista.controls.append(ft.Container(bgcolor="#111", border=ft.border.all(1, "#FF9800"), padding=6, border_radius=5, content=ft.Row([
                    ft.Column([ft.Text(s[1], size=12, weight="bold", color="#FF9800"), ft.Text(f"{s[2]} | {s[4]}", size=10)], expand=True),
                    ft.Text(f"R$ {s[3]:.2f}", size=11, color="#00ff41"),
                    ft.IconButton(ft.Icons.DELETE_FOREVER, icon_color="red", icon_size=18, on_click=lambda e, rowid=s[0]: (executar_query("DELETE FROM servicos WHERE ROWID=?", (rowid,)), carregar()))
                ])))
            page.update()
        carregar(); return ft.Column([ft.Text("HISTÓRICO", color="#FF9800"), lista])

    def tela_analytics():
        res_hoje = executar_query("SELECT SUM(valor) FROM servicos WHERE data = ?", (datetime.now().strftime("%d/%m/%Y"),), fetch=True)
        valor_hoje = res_hoje[0][0] if res_hoje and res_hoje[0][0] else 0
        def backup_manual(e):
            page.launch_url(f"file://{os.path.abspath(DB_PATH)}")
            page.snack_bar = ft.SnackBar(ft.Text("Caminho do Banco copiado para exportação!")); page.snack_bar.open = True; page.update()
        return ft.Column([
            ft.Text("DADOS", size=20, color="#4CAF50"),
            ft.Container(bgcolor="#111", padding=20, border_radius=10, content=ft.Column([
                ft.Text("LUCRO HOJE", size=12, color="white70"),
                ft.Text(f"R$ {valor_hoje:.2f}", size=35, weight="bold", color="#4CAF50")
            ], horizontal_alignment="center")),
            ft.Divider(height=40),
            ft.ElevatedButton("FAZER BACKUP DO BANCO (.DB)", icon=ft.Icons.STORAGE, bgcolor="#4CAF50", color="white", on_click=backup_manual, width=400)
        ], horizontal_alignment="center")

    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
            ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="Clientes"),
            ft.NavigationBarDestination(icon=ft.Icons.ADD_SHOPPING_CART, label="Check-in"),
            ft.NavigationBarDestination(icon=ft.Icons.CALENDAR_MONTH, label="Agenda"),
            ft.NavigationBarDestination(icon=ft.Icons.HISTORY, label="Histórico"),
            ft.NavigationBarDestination(icon=ft.Icons.ANALYTICS, label="Dados")
        ],
        on_change=lambda e: mudar_tela([tela_home(), tela_clientes(), tela_checkin(), tela_agenda(), tela_historico(), tela_analytics()][e.control.selected_index])
    )
    container_principal = ft.Container(content=tela_home(), expand=True, padding=20)
    page.add(container_principal)

ft.app(target=main)
