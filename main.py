import os, sqlite3, webbrowser, urllib.parse
import flet as ft
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURAÇÃO ---
DB_PATH = "black_car_service.db"
PASTA_RECIBOS = "comprovantes_black_car"
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

# Inicialização e Correção de Tabela
executar_query("CREATE TABLE IF NOT EXISTS base_clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, veiculo TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS servicos (cliente TEXT, veiculo TEXT, servico TEXT, valor REAL, data TEXT, obs TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS agendamentos (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, data TEXT, status TEXT)")

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

servicos_lista = [
    "Troca de Óleo e Filtros", "Revisão Geral (Checklist)", "Sistema de Freios", 
    "Suspensão e Amortecedores", "Embreagem", "Correia Dentada", "Limpeza de Injeção",
    "Arrefecimento (Radiador)", "Câmbio/Transmissão", "Elétrica / Bateria",
    "Ar Condicionado", "Alinhamento e Balanceamento", "Escapamento", "Scanner Diagnóstico",
    "Estética / Polimento", "Reparo de Motor"
]

def main(page: ft.Page):
    page.title = "Black Car Service Pro"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#050505"
    page.padding = 10
    dados_temp = {"nome": ""}

    def mudar_tela(view):
        container_principal.content = view
        page.update()

    def gerar_comprovante_e_whatsapp(cliente, veiculo, servico, valor, obs):
        img = Image.new('RGB', (600, 1000), color='#050505')
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 590, 990], outline="#e63946", width=8)
        try:
            f_titulo = ImageFont.truetype("arial.ttf", 45); f_label = ImageFont.truetype("arial.ttf", 22); f_texto = ImageFont.truetype("arial.ttf", 30)
        except:
            f_titulo = f_label = f_texto = ImageFont.load_default()
        
        draw.text((300, 100), "BLACK CAR SERVICE", fill="#e63946", font=f_titulo, anchor="ms")
        y = 220
        for label, texto in [("CLIENTE:", cliente), ("VEÍCULO:", veiculo), ("SERVIÇO:", servico), ("DATA:", datetime.now().strftime("%d/%m/%Y")), ("OBS:", obs)]:
            draw.text((60, y), label, fill="#e63946", font=f_label)
            draw.text((60, y + 35), str(texto), fill="white", font=f_texto)
            y += 110
        
        draw.rectangle([50, 800, 550, 910], fill="#111")
        draw.text((300, 855), f"TOTAL: R$ {valor:.2f}", fill="#00ff41", font=f_titulo, anchor="ms")
        
        nome_arq = f"Recibo_{cliente.replace(' ','_')}.png"
        img.save(os.path.join(PASTA_RECIBOS, nome_arq))
        
        msg_texto = f"🚀 *BLACK CAR SERVICE*\n\nOlá *{cliente}*, veículo *{veiculo}* pronto!\n🛠 *Serviço:* {servico}\n💰 *Total:* R$ {valor:.2f}"
        webbrowser.open(f"https://whatsapp.com{urllib.parse.quote(msg_texto)}")
        mudar_tela(tela_home())

    def tela_home():
        return ft.Column([ft.Container(height=60), ft.Text("🚗", size=80), ft.Text("BLACK CAR SERVICE", size=30, weight="bold", color="#e63946")], horizontal_alignment="center")

    def tela_checkin():
        res_c = executar_query("SELECT nome FROM base_clientes ORDER BY nome ASC", fetch=True)
        drop_cli = ft.Dropdown(label="Cliente", options=[ft.dropdown.Option(r[0]) for r in res_c])
        drop_srv = ft.Dropdown(label="Serviço", options=[ft.dropdown.Option(s) for s in servicos_lista])
        txt_val = ft.TextField(label="Valor", prefix=ft.Text("R$ "), keyboard_type=ft.KeyboardType.NUMBER)
        txt_obs = ft.TextField(label="Observações", multiline=True)

        def salvar(e, gerar):
            if not drop_cli.value: return
            try: val = float(txt_val.value.replace(",", "."))
            except: val = 0.0
            res_v = executar_query("SELECT veiculo FROM base_clientes WHERE nome=?", (drop_cli.value,), fetch=True)
            veic = res_v[0][0] if res_v else "Carro"
            executar_query("INSERT INTO servicos (cliente, veiculo, servico, valor, data, obs) VALUES (?,?,?,?,?,?)", (drop_cli.value, veic, drop_srv.value, val, datetime.now().strftime("%d/%m/%Y"), txt_obs.value))
            if gerar: gerar_comprovante_e_whatsapp(drop_cli.value, veic, drop_srv.value, val, txt_obs.value)
            else: mudar_tela(tela_home())

        return ft.Column([ft.Text("CHECK-IN", size=20, weight="bold"), drop_cli, drop_srv, txt_val, txt_obs, ft.ElevatedButton("FINALIZAR", on_click=lambda e: salvar(e, False), width=400), ft.ElevatedButton("FINALIZAR + RECIBO 📲", on_click=lambda e: salvar(e, True), width=400, bgcolor="#e63946", color="white")], scroll=ft.ScrollMode.ALWAYS)

    def tela_clientes():
        col = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=480, spacing=4)
        def carregar(f=""):
            col.controls.clear()
            # Usando ROWID para garantir que a coluna de ID funcione mesmo se a tabela for antiga
            for r in executar_query("SELECT ROWID, nome, veiculo FROM base_clientes WHERE nome LIKE ?", (f"%{f}%",), fetch=True):
                col.controls.append(ft.Container(bgcolor="#111", padding=6, border_radius=5, content=ft.Row([
                    ft.Column([ft.Text(r[1], size=13, weight="bold", color="#e63946"), ft.Text(r[2], size=10)], expand=True, spacing=0), 
                    ft.IconButton(ft.Icons.DELETE, icon_size=16, on_click=lambda e, cid=r[0]: (executar_query("DELETE FROM base_clientes WHERE ROWID=?", (cid,)), carregar()))
                ])))
            page.update()
        search = ft.TextField(label="Buscar cliente...", prefix_icon=ft.Icons.SEARCH, height=45, on_change=lambda e: carregar(e.control.value))
        carregar()
        return ft.Column([ft.Row([ft.Text("CLIENTES", size=18), ft.IconButton(ft.Icons.ADD, on_click=lambda _: abrir_modal_cad())], alignment="spaceBetween"), search, col])

    def abrir_modal_cad():
        dlg = ft.AlertDialog(title=ft.Text("Novo Cliente"))
        def p1():
            t = ft.TextField(label="Nome", capitalization=ft.TextCapitalization.CHARACTERS)
            dlg.content = t
            dlg.actions = [ft.TextButton("PRÓXIMO", on_click=lambda _: p2(t.value))]
            if dlg not in page.overlay: page.overlay.append(dlg)
            dlg.open = True; page.update()
        def p2(n):
            dados_temp["nome"] = n.upper()
            m = ft.Dropdown(label="Marca", options=[ft.dropdown.Option(x) for x in sorted(catalogo.keys())])
            dlg.content = m
            dlg.actions = [ft.TextButton("PRÓXIMO", on_click=lambda _: p3(m.value))]
            page.update()
        def p3(mrc):
            md = ft.Dropdown(label="Modelo", options=[ft.dropdown.Option(x) for x in sorted(catalogo[mrc])])
            dlg.content = md
            dlg.actions = [ft.TextButton("FIM", on_click=lambda _: (executar_query("INSERT INTO base_clientes (nome, veiculo) VALUES (?,?)", (dados_temp["nome"], f"{mrc} {md.value}")), setattr(dlg, "open", False), page.update(), mudar_tela(tela_clientes())))]
            page.update()
        p1()

    def tela_historico():
        lista = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=500, spacing=4)
        def carregar(f=""):
            lista.controls.clear()
            for s in executar_query("SELECT cliente, servico, valor, data FROM servicos WHERE cliente LIKE ? ORDER BY ROWID DESC", (f"%{f}%",), fetch=True):
                lista.controls.append(ft.Container(bgcolor="#111", padding=6, border_radius=5, content=ft.Row([
                    ft.Column([ft.Text(s[0], size=12, weight="bold", color="#e63946"), ft.Text(f"{s[1]} | {s[3]}", size=10)], expand=True, spacing=0), 
                    ft.Text(f"R$ {s[2]:.2f}", size=11, weight="bold", color="#00ff41")
                ])))
            page.update()
        search_h = ft.TextField(label="Buscar histórico...", height=45, on_change=lambda e: carregar(e.control.value))
        carregar(); return ft.Column([ft.Row([ft.Text("HISTÓRICO"), ft.IconButton(ft.Icons.DELETE_SWEEP, icon_size=20, on_click=lambda _: (executar_query("DELETE FROM servicos"), carregar()))], alignment="spaceBetween"), search_h, lista])

    def tela_analytics():
        res_hoje = executar_query("SELECT SUM(valor) FROM servicos WHERE data = ?", (datetime.now().strftime("%d/%m/%Y"),), fetch=True)
        valor_hoje = res_hoje[0][0] if res_hoje and res_hoje[0][0] else 0
        return ft.Column([ft.Text("DADOS", size=20, weight="bold"), ft.Container(bgcolor="#111", padding=20, border_radius=10, content=ft.Column([
            ft.Text("HOJE", size=12, color="white70"), ft.Text(f"R$ {valor_hoje:.2f}", size=30, weight="bold", color="#00ff41")
        ], horizontal_alignment="center"))], horizontal_alignment="center")

    def tela_agenda():
        col_ag = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=400, spacing=4)
        def carregar_agenda():
            col_ag.controls.clear()
            for a in executar_query("SELECT ROWID, cliente, data FROM agendamentos WHERE status = 'ABERTO' ORDER BY data ASC", fetch=True):
                col_ag.controls.append(ft.Container(bgcolor="#111", padding=10, border_radius=5, content=ft.Row([
                    ft.Column([ft.Text(a[1], size=14, weight="bold", color="#e63946"), ft.Text(a[2], size=12)], expand=True),
                    ft.IconButton(ft.Icons.CHECK, icon_color="#00ff41", on_click=lambda e, id_ag=a[0]: (executar_query("UPDATE agendamentos SET status='CONCLUIDO' WHERE ROWID=?", (id_ag,)), carregar_agenda()))
                ])))
            page.update()

        res_c = executar_query("SELECT nome FROM base_clientes ORDER BY nome ASC", fetch=True)
        drop_ag = ft.Dropdown(label="Cliente", options=[ft.dropdown.Option(c[0]) for c in res_c])
        btn_d = ft.ElevatedButton("Data", on_click=lambda _: (setattr(dp, "open", True), page.update()))
        dp = ft.DatePicker(on_change=lambda e: (setattr(btn_d, "text", e.control.value.strftime("%d/%m/%Y")), page.update()))
        
        def agendar_evento(e):
            if drop_ag.value and btn_d.text != "Data":
                executar_query("INSERT INTO agendamentos (cliente, data, status) VALUES (?,?,?)", (drop_ag.value, btn_d.text, 'ABERTO'))
                page.snack_bar = ft.SnackBar(ft.Text("Agendado!")); page.snack_bar.open = True
                carregar_agenda()

        page.overlay.append(dp)
        carregar_agenda()
        return ft.Column([ft.Text("AGENDA", size=20, weight="bold"), drop_ag, btn_d, ft.ElevatedButton("AGENDAR SERVIÇO", width=400, bgcolor="#e63946", color="white", on_click=agendar_evento), ft.Divider(), ft.Text("PRÓXIMOS SERVIÇOS", size=16), col_ag])

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
