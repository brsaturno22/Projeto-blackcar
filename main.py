import os, sqlite3, webbrowser
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
    finally:
        conn.close()

# Inicialização do Banco
executar_query("CREATE TABLE IF NOT EXISTS base_clientes (id INTEGER PRIMARY KEY, nome TEXT, veiculo TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS servicos (cliente TEXT, veiculo TEXT, servico TEXT, valor REAL, data TEXT, obs TEXT)")
executar_query("CREATE TABLE IF NOT EXISTS agendamentos (cliente TEXT, data TEXT, hora TEXT, status TEXT)")
try: executar_query("ALTER TABLE servicos ADD COLUMN obs TEXT")
except: pass

catalogo = {
    "Toyota": ["Corolla", "Hilux", "SW4", "Etios"], "VW": ["Gol", "Polo", "Jetta", "Nivus"],
    "Chevrolet": ["Onix", "S10", "Cruze", "Tracker"], "Fiat": ["Strada", "Toro", "Argo", "Mobi"],
    "Honda": ["Civic", "HR-V", "Fit"], "Hyundai": ["HB20", "Creta"], "Jeep": ["Renegade", "Compass"],
    "Renault": ["Sandero", "Duster", "Kwid"]
}
servicos_lista = ["Troca de Óleo", "Revisão Geral", "Freios", "Suspensão", "Estética", "Alinhamento"]

def main(page: ft.Page):
    page.title = "Black Car Service Pro"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#050505"
    page.padding = 10
    dados_temp = {"nome": ""}

    def mudar_tela(view):
        container_principal.content = view
        page.update()

    # --- RECIBO ---
    def gerar_comprovante_e_whatsapp(cliente, veiculo, servico, valor, obs):
        img = Image.new('RGB', (600, 950), color='#050505')
        draw = ImageDraw.Draw(img)
        # CORREÇÃO DA SINTAXE AQUI:
        draw.rectangle([10, 10, 590, 940], outline="#e63946", width=5)
        
        try:
            f_titulo = ImageFont.truetype("arial.ttf", 40)
            f_texto = ImageFont.truetype("arial.ttf", 25)
        except: f_titulo = f_texto = ImageFont.load_default()
        
        draw.text((300, 80), "BLACK CAR SERVICE", fill="#e63946", font=f_titulo, anchor="ms")
        y = 200
        for label, texto in [("CLIENTE", cliente), ("VEÍCULO", veiculo), ("SERVIÇO", servico), ("DATA", datetime.now().strftime("%d/%m/%Y"))]:
            draw.text((60, y), label, fill="#e63946", font=f_texto)
            draw.text((60, y + 35), str(texto), fill="white", font=f_texto)
            y += 90
        
        draw.rectangle([50, 750, 550, 840], fill="#111")
        draw.text((300, 795), f"TOTAL: R$ {valor:.2f}", fill="#00ff41", font=f_titulo, anchor="ms")
        
        nome_arq = f"Recibo_{cliente.replace(' ','_')}_{datetime.now().strftime('%H%M')}.png"
        img.save(os.path.join(PASTA_RECIBOS, nome_arq))
        msg = f"Olá {cliente}, serviço concluído! {servico}. Total: R$ {valor:.2f}.".replace(" ", "%20")
        webbrowser.open(f"https://wa.me{msg}")
        mudar_tela(tela_home())

    # --- TELAS ---
    def tela_home():
        return ft.Column([ft.Container(height=60), ft.Text("🚗", size=80), ft.Text("BLACK CAR SERVICE", size=30, weight="bold", color="#e63946")], horizontal_alignment="center")

    def tela_checkin():
        res_c = executar_query("SELECT nome FROM base_clientes ORDER BY nome ASC", fetch=True)
        drop_cli = ft.Dropdown(label="Cliente", options=[ft.dropdown.Option(r[0]) for r in res_c])
        drop_srv = ft.Dropdown(label="Serviço", options=[ft.dropdown.Option(s) for s in servicos_lista])
        txt_val = ft.TextField(label="Valor", prefix=ft.Text("R$ "))
        txt_obs = ft.TextField(label="Observações", multiline=True)

        def salvar(gerar):
            val = float(txt_val.value.replace(",", "."))
            res_v = executar_query("SELECT veiculo FROM base_clientes WHERE nome=?", (drop_cli.value,), fetch=True)
            veic = res_v[0][0] if res_v else "Carro"
            executar_query("INSERT INTO servicos (cliente, veiculo, servico, valor, data, obs) VALUES (?,?,?,?,?,?)", (drop_cli.value, veic, drop_srv.value, val, datetime.now().strftime("%d/%m/%Y"), txt_obs.value))
            if gerar: gerar_comprovante_e_whatsapp(drop_cli.value, veic, drop_srv.value, val, txt_obs.value)
            else: mudar_tela(tela_home())

        return ft.Column([ft.Text("CHECK-IN", size=20, weight="bold"), drop_cli, drop_srv, txt_val, txt_obs, ft.ElevatedButton("FINALIZAR", on_click=lambda _: salvar(False), width=400), ft.ElevatedButton("FINALIZAR + RECIBO", on_click=lambda _: salvar(True), width=400, bgcolor="#e63946")], scroll=ft.ScrollMode.ALWAYS)

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
        search = ft.TextField(label="Buscar cliente...", prefix_icon=ft.Icons.SEARCH, height=45, text_size=14, on_change=lambda e: carregar(e.control.value))
        carregar()
        return ft.Column([ft.Row([ft.Text("CLIENTES", size=18), ft.IconButton(ft.Icons.ADD, on_click=lambda _: abrir_modal_cad())], alignment="spaceBetween"), search, col])

    def abrir_modal_cad():
        dlg = ft.AlertDialog(title=ft.Text("Novo Cliente"))
        def p1():
            t = ft.TextField(label="Nome"); dlg.content = t
            dlg.actions = [ft.TextButton("PRÓXIMO", on_click=lambda _: p2(t.value))]; page.overlay.append(dlg); dlg.open = True; page.update()
        def p2(n):
            dados_temp["nome"] = n.upper()
            m = ft.Dropdown(label="Marca", options=[ft.dropdown.Option(x) for x in catalogo.keys()]); dlg.content = m
            dlg.actions = [ft.TextButton("PRÓXIMO", on_click=lambda _: p3(m.value))]; page.update()
        def p3(mrc):
            md = ft.Dropdown(label="Modelo", options=[ft.dropdown.Option(x) for x in catalogo[mrc]]); dlg.content = md
            dlg.actions = [ft.TextButton("FIM", on_click=lambda _: (executar_query("INSERT INTO base_clientes (nome, veiculo) VALUES (?,?)", (dados_temp["nome"], f"{mrc} {md.value}")), setattr(dlg, "open", False), mudar_tela(tela_clientes())))]; page.update()
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
        search_h = ft.TextField(label="Buscar histórico...", height=45, text_size=14, on_change=lambda e: carregar(e.control.value))
        carregar(); return ft.Column([ft.Row([ft.Text("HISTÓRICO"), ft.IconButton(ft.Icons.DELETE_SWEEP, icon_size=20, on_click=lambda _: (executar_query("DELETE FROM servicos"), carregar()))], alignment="spaceBetween"), search_h, lista])

    def tela_analytics():
        hoje = datetime.now().strftime("%d/%m/%Y")
        mes_atual = datetime.now().strftime("/%m/%Y")
        
        res_hoje = executar_query("SELECT SUM(valor) FROM servicos WHERE data = ?", (hoje,), fetch=True)
        valor_hoje = res_hoje[0][0] if res_hoje[0][0] else 0
        
        res_mes = executar_query("SELECT SUM(valor) FROM servicos WHERE data LIKE ?", (f"%{mes_atual}",), fetch=True)
        valor_mes = res_mes[0][0] if res_mes[0][0] else 0
        
        return ft.Column([
            ft.Text("DADOS", size=20, weight="bold"),
            ft.Container(bgcolor="#111", padding=20, border_radius=10, content=ft.Column([
                ft.Text("HOJE", size=12, color="white70"),
                ft.Text(f"R$ {valor_hoje:.2f}", size=30, weight="bold", color="#00ff41"),
                ft.Divider(color="white10"),
                ft.Text("MENSAL", size=12, color="white70"),
                ft.Text(f"R$ {valor_mes:.2f}", size=25, weight="bold", color="#ffbe0b"),
            ], horizontal_alignment="center"))
        ], horizontal_alignment="center")

    page.navigation_bar = ft.NavigationBar(
        destinations=[ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"), ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="Clientes"), ft.NavigationBarDestination(icon=ft.Icons.ADD_SHOPPING_CART, label="Check-in"), ft.NavigationBarDestination(icon=ft.Icons.CALENDAR_MONTH, label="Agenda"), ft.NavigationBarDestination(icon=ft.Icons.HISTORY, label="Histórico"), ft.NavigationBarDestination(icon=ft.Icons.ANALYTICS, label="Dados")],
        on_change=lambda e: mudar_tela([tela_home(), tela_clientes(), tela_checkin(), tela_agenda(), tela_historico(), tela_analytics()][e.control.selected_index])
    )
    container_principal = ft.Container(content=tela_home(), expand=True, padding=20)
    page.add(container_principal)

def tela_agenda():
    # Mantendo a estrutura solicitada anteriormente
    res_c = executar_query("SELECT nome FROM base_clientes ORDER BY nome ASC", fetch=True)
    drop_ag = ft.Dropdown(label="Cliente", options=[ft.dropdown.Option(c[0]) for c in res_c])
    btn_d = ft.ElevatedButton("Data", on_click=lambda _: (setattr(dp, "open", True), page.update()))
    dp = ft.DatePicker(on_change=lambda e: (setattr(btn_d, "text", e.control.value.strftime("%d/%m/%Y")), page.update()))
    # Note: page deve estar no escopo ou ser passada
    return ft.Column([ft.Text("AGENDA"), drop_ag, btn_d, ft.ElevatedButton("AGENDAR")])

ft.app(target=main)
