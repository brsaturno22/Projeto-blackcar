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

executar_query("CREATE TABLE IF NOT EXISTS base_clientes (id INTEGER PRIMARY KEY, nome TEXT, veiculo TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS servicos (cliente TEXT, veiculo TEXT, servico TEXT, valor REAL, data TEXT, obs TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS agendamentos (cliente TEXT, data TEXT, hora TEXT, status TEXT)")

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

    # --- RECIBO PROFISSIONAL E WHATSAPP ---
    def gerar_comprovante_e_whatsapp(cliente, veiculo, servico, valor, obs):
        # 1. Criação do Recibo Visual (Melhorado)
        img = Image.new('RGB', (600, 1000), color='#050505')
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 590, 990], outline="#e63946", width=8) # Borda mais grossa
        
        try:
            f_titulo = ImageFont.truetype("arial.ttf", 45)
            f_label = ImageFont.truetype("arial.ttf", 22)
            f_texto = ImageFont.truetype("arial.ttf", 30)
        except:
            f_titulo = f_label = f_texto = ImageFont.load_default()
        
        draw.text((300, 100), "BLACK CAR SERVICE", fill="#e63946", font=f_titulo, anchor="ms")
        draw.line([50, 130, 550, 130], fill="white", width=2)
        
        y = 220
        dados_recibo = [
            ("CLIENTE:", cliente),
            ("VEÍCULO:", veiculo),
            ("SERVIÇO:", servico),
            ("DATA:", datetime.now().strftime("%d/%m/%Y")),
            ("OBSERVAÇÕES:", obs if obs else "Nenhuma")
        ]
        
        for label, texto in dados_recibo:
            draw.text((60, y), label, fill="#e63946", font=f_label)
            draw.text((60, y + 35), str(texto), fill="white", font=f_texto)
            y += 110
        
        draw.rectangle([50, 800, 550, 900], fill="#111")
        draw.text((300, 855), f"TOTAL: R$ {valor:.2f}", fill="#00ff41", font=f_titulo, anchor="ms")
        
        nome_arq = f"Recibo_{cliente.replace(' ','_')}_{datetime.now().strftime('%H%M')}.png"
        img_path = os.path.join(PASTA_RECIBOS, nome_arq)
        img.save(img_path)
        
        # 2. Envio via WhatsApp (Link Corrigido para Mobile)
        msg_texto = f"🚀 *BLACK CAR SERVICE*\n\nOlá *{cliente}*, seu veículo *{veiculo}* está pronto!\n🛠 *Serviço:* {servico}\n💰 *Valor:* R$ {valor:.2f}\n📅 *Data:* {datetime.now().strftime('%d/%m/%Y')}\n\nAgradecemos a preferência!"
        msg_encoded = urllib.parse.quote(msg_texto)
        whatsapp_url = f"https://whatsapp.com{msg_encoded}"
        
        try:
            webbrowser.open(whatsapp_url)
        except:
            print("Não foi possível abrir o WhatsApp automaticamente.")
        
        mudar_tela(tela_home())

    def tela_home():
        return ft.Column([ft.Container(height=60), ft.Text("🚗", size=80), ft.Text("BLACK CAR SERVICE", size=30, weight="bold", color="#e63946")], horizontal_alignment="center")

    def tela_checkin():
        res_c = executar_query("SELECT nome FROM base_clientes ORDER BY nome ASC", fetch=True)
        drop_cli = ft.Dropdown(label="Cliente", options=[ft.dropdown.Option(r[0]) for r in res_c])
        drop_srv = ft.Dropdown(label="Serviço", options=[ft.dropdown.Option(s) for s in servicos_lista])
        txt_val = ft.TextField(label="Valor", prefix=ft.Text("R$ "), keyboard_type=ft.KeyboardType.NUMBER)
        txt_obs = ft.TextField(label="Observações", multiline=True)

        def salvar_servico(e, gerar_recibo):
            if not drop_cli.value or not drop_srv.value:
                page.snack_bar = ft.SnackBar(ft.Text("Selecione Cliente e Serviço!"))
                page.snack_bar.open = True
                page.update()
                return

            try: val = float(txt_val.value.replace(",", "."))
            except: val = 0.0
            
            res_v = executar_query("SELECT veiculo FROM base_clientes WHERE nome=?", (drop_cli.value,), fetch=True)
            veic = res_v[0][0] if res_v else "Carro"
            
            executar_query("INSERT INTO servicos (cliente, veiculo, servico, valor, data, obs) VALUES (?,?,?,?,?,?)", 
                          (drop_cli.value, veic, drop_srv.value, val, datetime.now().strftime("%d/%m/%Y"), txt_obs.value))
            
            if gerar_recibo:
                gerar_comprovante_e_whatsapp(drop_cli.value, veic, drop_srv.value, val, txt_obs.value)
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Serviço registrado com sucesso!"))
                page.snack_bar.open = True
                mudar_tela(tela_home())

        return ft.Column([
            ft.Text("CHECK-IN", size=20, weight="bold"),
            drop_cli, drop_srv, txt_val, txt_obs,
            ft.ElevatedButton("FINALIZAR (SEM RECIBO)", on_click=lambda e: salvar_servico(e, False), width=400),
            ft.ElevatedButton("FINALIZAR + RECIBO 📲", on_click=lambda e: salvar_servico(e, True), width=400, bgcolor="#e63946", color="white")
        ], scroll=ft.ScrollMode.ALWAYS)

    # --- DEMAIS TELAS (Mantidas Conforme Código Anterior) ---
    def tela_clientes():
        col = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=480, spacing=4)
        def carregar(f=""):
            col.controls.clear()
            for r in executar_query("SELECT id, nome, veiculo FROM base_clientes WHERE nome LIKE ?", (f"%{f}%",), fetch=True):
                col.controls.append(ft.Container(bgcolor="#111", padding=6, border_radius=5, content=ft.Row([
                    ft.Column([ft.Text(r[1], size=13, weight="bold", color="#e63946"), ft.Text(r[2], size=10)], expand=True, spacing=0),
                    ft.IconButton(ft.Icons.DELETE, icon_size=16, on_click=lambda e, id_c=r[0]: (executar_query("DELETE FROM base_clientes WHERE id=?", (id_c,)), carregar()))
                ])))
            page.update()
        search = ft.TextField(label="Buscar cliente...", prefix_icon=ft.Icons.SEARCH, height=45, on_change=lambda e: carregar(e.control.value))
        carregar()
        return ft.Column([ft.Row([ft.Text("CLIENTES", size=18), ft.IconButton(ft.Icons.ADD, on_click=lambda _: abrir_modal_cad())], alignment="spaceBetween"), search, col])

    def abrir_modal_cad():
        def fechar_dlg(e):
            dlg.open = False
            page.update()
        dlg = ft.AlertDialog(title=ft.Text("Novo Cliente"))
        def p1():
            t = ft.TextField(label="Nome"); dlg.content = t
            dlg.actions = [ft.TextButton("PRÓXIMO", on_click=lambda _: p2(t.value))]; page.dialog = dlg; dlg.open = True; page.update()
        def p2(n):
            dados_temp["nome"] = n.upper()
            m = ft.Dropdown(label="Marca", options=[ft.dropdown.Option(x) for x in sorted(catalogo.keys())]); dlg.content = m
            dlg.actions = [ft.TextButton("PRÓXIMO", on_click=lambda _: p3(m.value))]; page.update()
        def p3(mrc):
            md = ft.Dropdown(label="Modelo", options=[ft.dropdown.Option(x) for x in sorted(catalogo[mrc])]); dlg.content = md
            dlg.actions = [ft.TextButton("FIM", on_click=lambda _: (executar_query("INSERT INTO base_clientes (nome, veiculo) VALUES (?,?)", (dados_temp["nome"], f"{mrc} {md.value}")), fechar_dlg(None), mudar_tela(tela_clientes())))]; page.update()
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
        hoje = datetime.now().strftime("%d/%m/%Y")
        mes_atual = datetime.now().strftime("/%m/%Y")
        res_hoje = executar_query("SELECT SUM(valor) FROM servicos WHERE data = ?", (hoje,), fetch=True)
        valor_hoje = res_hoje[0][0] if res_hoje[0][0] else 0
        res_mes = executar_query("SELECT SUM(valor) FROM servicos WHERE data LIKE ?", (f"%{mes_atual}",), fetch=True)
        valor_mes = res_mes[0][0] if res_mes[0][0] else 0
        return ft.Column([ ft.Text("DADOS", size=20, weight="bold"), ft.Container(bgcolor="#111", padding=20, border_radius=10, content=ft.Column([
            ft.Text("HOJE", size=12, color="white70"), ft.Text(f"R$ {valor_hoje:.2f}", size=30, weight="bold", color="#00ff41"),
            ft.Divider(color="white10"), ft.Text("MENSAL", size=12, color="white70"), ft.Text(f"R$ {valor_mes:.2f}", size=25, weight="bold", color="#ffbe0b"),
        ], horizontal_alignment="center")) ], horizontal_alignment="center")

    def tela_agenda():
        res_c = executar_query("SELECT nome FROM base_clientes ORDER BY nome ASC", fetch=True)
        drop_ag = ft.Dropdown(label="Cliente", options=[ft.dropdown.Option(c[0]) for c in res_c])
        btn_d = ft.ElevatedButton("Data", on_click=lambda _: (setattr(dp, "open", True), page.update()))
        dp = ft.DatePicker(on_change=lambda e: (setattr(btn_d, "text", e.control.value.strftime("%d/%m/%Y")), page.update()))
        page.overlay.append(dp)
        return ft.Column([ft.Text("AGENDA"), drop_ag, btn_d, ft.ElevatedButton("AGENDAR")])

    page.navigation_bar = ft.NavigationBar(
        destinations=[ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"), 
                      ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="Clientes"), 
                      ft.NavigationBarDestination(icon=ft.Icons.ADD_SHOPPING_CART, label="Check-in"), 
                      ft.NavigationBarDestination(icon=ft.Icons.CALENDAR_MONTH, label="Agenda"), 
                      ft.NavigationBarDestination(icon=ft.Icons.HISTORY, label="Histórico"), 
                      ft.NavigationBarDestination(icon=ft.Icons.ANALYTICS, label="Dados")],
        on_change=lambda e: mudar_tela([tela_home(), tela_clientes(), tela_checkin(), tela_agenda(), tela_historico(), tela_analytics()][e.control.selected_index])
    )
    container_principal = ft.Container(content=tela_home(), expand=True, padding=20)
    page.add(container_principal)

ft.app(target=main)
