#!/usr/bin/env python3
import os
import json
import smtplib
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from ttkbootstrap import Window, ttk
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from PIL import Image, ImageTk
from email.mime.image import MIMEImage
from ttkbootstrap.scrolled import ScrolledText
from tkhtmlview import HTMLLabel
from cryptography.fernet import Fernet

# -------------------- VARIÁVEIS GLOBAIS --------------------
grupos_path = "data/grupos.json"
historico_path = "data/historico.json"
modelos_path = "data/modelos.json"
anexos = []
senha_remetente = ""
email_remetente = ""
imagem_inline_path = None

# ---------------- FUNÇÕES ÚTEIS ----------------
def carregar_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_json(path, dados):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

def gerar_chave():
    chave = Fernet.generate_key()
    with open("chave.key", "wb") as f:
        f.write(chave)
    return chave

def carregar_chave():
    if os.path.exists("chave.key"):
        with open("chave.key", "rb") as f:
            return f.read()
    return gerar_chave()

def salvar_login_criptografado(email, senha):
    chave = carregar_chave()
    fernet = Fernet(chave)
    dados = json.dumps({"email": email, "senha": senha}).encode()
    dados_criptografados = fernet.encrypt(dados)
    with open("login_criptografado.bin", "wb") as f:
        f.write(dados_criptografados)

def carregar_login_criptografado():
    if not os.path.exists("login_criptografado.bin"):
        return "", ""
    chave = carregar_chave()
    fernet = Fernet(chave)
    with open("login_criptografado.bin", "rb") as f:
        dados_criptografados = f.read()
    try:
        dados = fernet.decrypt(dados_criptografados).decode()
        info = json.loads(dados)
        return info.get("email", ""), info.get("senha", "")
    except:
        return "", ""

# ---------------- SPLASH E LOGIN ----------------
def splash_screen(root, on_close_callback):
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.geometry("400x300+600+300")
    splash.configure(bg="white")

    try:
        imagem = Image.open("logo.png")
        imagem = imagem.resize((100, 100))
        logo = ImageTk.PhotoImage(imagem)
        logo_label = tk.Label(splash, image=logo, bg="white")
        logo_label.image = logo
        logo_label.pack(pady=(30, 10))
    except Exception as e:
        print("Erro ao carregar imagem:", e)

    tk.Label(splash, text="Iniciando sistema...", font=("Helvetica", 14), bg="white").pack()

    barra = ttk.Progressbar(splash, mode="indeterminate", bootstyle="info-striped")
    barra.pack(padx=30, pady=20, fill='x')
    barra.start(10)

    root.after(2500, lambda: fechar_splash(splash, barra, on_close_callback))

def fechar_splash(splash, barra, callback):
    barra.stop()
    splash.destroy()
    callback()

def tela_login(root):
    global email_remetente, senha_remetente

    login_win = tk.Toplevel(root)
    login_win.title("Login")
    login_win.geometry("320x250")
    login_win.resizable(False, False)

    ttk.Label(login_win, text="Seu Gmail:").pack(pady=5)
    email_entry = ttk.Entry(login_win, width=30)
    email_entry.pack()

    ttk.Label(login_win, text="Senha do App Gmail:").pack(pady=5)
    senha_entry = ttk.Entry(login_win, show="*", width=30)
    senha_entry.pack()

    lembrar_var = tk.BooleanVar(value=False)
    lembrar_check = ttk.Checkbutton(login_win, text="Lembrar-me", variable=lembrar_var, bootstyle="info")
    lembrar_check.pack(pady=5)

    email_salvo, senha_salva = carregar_login_criptografado()
    if email_salvo and senha_salva:
        email_entry.insert(0, email_salvo)
        senha_entry.insert(0, senha_salva)
        lembrar_var.set(True)

    def validar():
        global email_remetente, senha_remetente
        email = email_entry.get().strip()
        senha = senha_entry.get().strip()
        if not email or not senha:
            messagebox.showerror("Erro", "Preencha todos os campos.", parent=login_win)
            return

        if lembrar_var.get():
            salvar_login_criptografado(email, senha)
        else:
            if os.path.exists("login_criptografado.bin"):
                os.remove("login_criptografado.bin")

        email_remetente = email
        senha_remetente = senha
        login_win.destroy()
        root.deiconify()

    ttk.Button(login_win, text="Entrar", command=validar, bootstyle="success-outline").pack(pady=15)

    root.withdraw()
    root.wait_window(login_win)

# ---------------- FUNCIONALIDADES PRINCIPAIS ----------------
def registrar_envio(grupo, assunto):
    historico = carregar_json(historico_path)
    if not isinstance(historico, list):
        historico = []
    historico.append({
        "grupo": grupo,
        "assunto": assunto,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M")
    })
    salvar_json(historico_path, historico)

def exportar_historico():
    if not os.path.exists(historico_path):
        messagebox.showinfo("Histórico", "Nenhum histórico encontrado.")
        return
    file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
    if not file:
        return
    dados = carregar_json(historico_path)
    with open(file, "w", encoding="utf-8") as f:
        f.write("Grupo,Assunto,Data\n")
        for item in dados:
            f.write(f"{item['grupo']},{item['assunto']},{item['data']}\n")
    messagebox.showinfo("Exportado", f"Histórico exportado para:\n{file}")

def selecionar_anexo(listbox):
    file_path = filedialog.askopenfilename()
    if file_path:
        anexos.append(file_path)
        listbox.insert(tk.END, os.path.basename(file_path))

def remover_anexo(listbox):
    selecao = listbox.curselection()
    if selecao:
        index = selecao[0]
        anexos.pop(index)
        listbox.delete(index)

def selecionar_imagem_inline():
    global imagem_inline_path
    imagem_inline_path = filedialog.askopenfilename(filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.gif")])
    if imagem_inline_path:
        messagebox.showinfo("Imagem selecionada", f"Imagem inline selecionada:\n{os.path.basename(imagem_inline_path)}")

def agendar_envio(grupo, assunto, mensagem, horario_str):
    try:
        horario = datetime.strptime(horario_str.strip(), "%H:%M").time()
    except ValueError:
        messagebox.showerror("Erro", "Formato inválido. Use HH:MM")
        return
    def verificador():
        while True:
            agora = datetime.now().time()
            if agora >= horario:
                enviar_emails(grupo, assunto, mensagem, anexos.copy())
                break
            time.sleep(30)
    threading.Thread(target=verificador, daemon=True).start()
    messagebox.showinfo("Agendamento", f"E-mail agendado para {horario_str}")

def salvar_novo_grupo(entry, text, atualizar_func):
    nome = entry.get().strip()
    contatos = [linha.strip() for linha in text.get("1.0", tk.END).strip().splitlines() if linha.strip()]
    if nome and contatos:
        grupos = carregar_json(grupos_path)
        grupos[nome] = contatos
        salvar_json(grupos_path, grupos)
        entry.delete(0, tk.END)
        text.delete("1.0", tk.END)
        atualizar_func()
        messagebox.showinfo("Grupo", f"Grupo '{nome}' salvo com sucesso.")
    else:
        messagebox.showerror("Erro", "Preencha o nome e contatos.")

# ---------------- ENVIO DE EMAIL COM PROGRESSO ----------------
def enviar_emails(grupo_nome, assunto, mensagem, anexos_local, email_individual=None, whatsapp_numero=None):
    def executar_envio(progress_win, barra):
        try:
            grupos = carregar_json(grupos_path)
            contatos = grupos.get(grupo_nome, [])
            if email_individual:
                contatos = [email_individual]
            if not contatos:
                messagebox.showerror("Erro", "Nenhum contato selecionado.")
                progress_win.destroy()
                return

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(email_remetente, senha_remetente)

            total = len(contatos)
            for i, email in enumerate(contatos, 1):
                nome = email.split("@")[0]

                msg = MIMEMultipart("mixed")
                msg["From"] = email_remetente
                msg["To"] = email
                msg["Subject"] = assunto

                related_part = MIMEMultipart("related")
                alternative_part = MIMEMultipart("alternative")

                corpo_html = ""
                if imagem_inline_path:
                    corpo_html += '<img src="cid:imagem1"><br><br>'
                corpo_html += mensagem.replace("{nome}", nome)
                if whatsapp_numero:
                    corpo_html += (
                        f"<br><br><a href='https://wa.me/{whatsapp_numero}' "
                        "style='padding:10px 20px; background:#25D366; color:white; "
                        "text-decoration:none; border-radius:5px;'>Fale conosco no WhatsApp</a>"
                    )

                alternative_part.attach(MIMEText(corpo_html, "html"))
                related_part.attach(alternative_part)

                if imagem_inline_path:
                    with open(imagem_inline_path, 'rb') as img_file:
                        img = MIMEImage(img_file.read())
                        img.add_header('Content-ID', '<imagem1>')
                        img.add_header('Content-Disposition', 'inline', filename=os.path.basename(imagem_inline_path))
                        related_part.attach(img)

                msg.attach(related_part)

                for path in anexos_local:
                    with open(path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(path))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(path)}"'
                        msg.attach(part)

                server.send_message(msg)
                barra["value"] = (i / total) * 100
                progress_win.update()

            server.quit()
            registrar_envio(grupo_nome, assunto)
            progress_win.destroy()
            messagebox.showinfo("Sucesso", "E-mails enviados com sucesso!")
        except Exception as e:
            progress_win.destroy()
            messagebox.showerror("Erro", f"Falha no envio:\n{e}")

    progress_win = tk.Toplevel()
    progress_win.title("Enviando e-mails")
    ttk.Label(progress_win, text="Enviando e-mails...").pack(pady=10)
    barra = ttk.Progressbar(progress_win, mode="determinate", length=300)
    barra.pack(pady=10)
    threading.Thread(target=executar_envio, args=(progress_win, barra), daemon=True).start()

# ---------------- TEMPLATES ----------------
def salvar_template(nome, mensagem):
    if not nome:
        messagebox.showerror("Erro", "Nome do modelo não pode ser vazio.")
        return
    modelos = carregar_json(modelos_path)
    modelos[nome] = mensagem
    salvar_json(modelos_path, modelos)
    messagebox.showinfo("Modelo", f"Modelo '{nome}' salvo com sucesso.")

def carregar_template(mensagem_text):
    modelos = carregar_json(modelos_path)
    if not modelos:
        messagebox.showinfo("Modelos", "Nenhum modelo salvo.")
        return
    win = tk.Toplevel()
    win.title("Selecionar Modelo")
    ttk.Label(win, text="Escolha um modelo:").pack(pady=5)
    lista = ttk.Combobox(win, values=list(modelos.keys()), state="readonly")
    lista.pack(pady=5)
    def aplicar():
        selecionado = lista.get()
        if selecionado:
            mensagem_text.delete("1.0", tk.END)
            mensagem_text.insert("1.0", modelos[selecionado])
            win.destroy()
    ttk.Button(win, text="Usar Modelo", command=aplicar).pack(pady=10)

# ---------------- INTERFACE ----------------
def iniciar_interface(root):
    global grupos_var, grupos_menu, assunto_entry, mensagem_text, anexos_listbox, grupo_nome_entry, grupo_contatos_text, horario_entry

    root.title("Bot de Disparo de E-mails")
    root.geometry("800x850")

    # Frame principal com canvas rolável
    container = ttk.Frame(root)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    # Atualiza região de rolagem sempre que o frame interno mudar
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    # Criar janela dentro do canvas (centralizada)
    window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="n")

    # Ajustar largura automaticamente para centralizar
    def on_resize(event):
        canvas.itemconfig(window_id, width=event.width)
    canvas.bind("<Configure>", on_resize)

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Agora você adiciona tudo dentro de "frame"
    frame = scrollable_frame

    # Grupo contatos
    ttk.Label(frame, text="Grupo de Contatos:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
    grupos_var = tk.StringVar()
    grupos_menu = ttk.Combobox(frame, textvariable=grupos_var, state="readonly")
    grupos_menu.pack(fill="x", pady=2)

    def atualizar_menu():
        grupos = carregar_json(grupos_path)
        nomes = list(grupos.keys())
        grupos_menu['values'] = nomes
        if nomes:
            grupos_var.set(nomes[0])
        else:
            grupos_var.set("")

    atualizar_menu()

    # Lista contatos do grupo com busca
    ttk.Label(frame, text="Buscar Contato no Grupo:").pack(anchor="w", pady=(10, 0))
    search_var = tk.StringVar()
    search_entry = ttk.Entry(frame, textvariable=search_var)
    search_entry.pack(fill="x", pady=2)

    lista = tk.Listbox(frame, height=5)
    lista.pack(fill="x")

    def atualizar_lista_contatos(event=None):
        grupo = grupos_var.get()
        termo = search_var.get().strip().lower()
        grupos = carregar_json(grupos_path)
        contatos = grupos.get(grupo, [])
        lista.delete(0, tk.END)
        for c in contatos:
            if termo in c.lower():
                lista.insert(tk.END, c)

    grupos_menu.bind("<<ComboboxSelected>>", atualizar_lista_contatos)
    search_var.trace_add("write", lambda *args: atualizar_lista_contatos())
    atualizar_lista_contatos()

    def remover_grupo():
        grupo = grupos_var.get()
        if not grupo:
            messagebox.showerror("Erro", "Nenhum grupo selecionado.")
            return
        if messagebox.askyesno("Remover", f"Deseja remover o grupo '{grupo}'?"):
            grupos = carregar_json(grupos_path)
            if grupo in grupos:
                del grupos[grupo]
                salvar_json(grupos_path, grupos)
                atualizar_menu()
                messagebox.showinfo("Removido", f"Grupo '{grupo}' removido.")
                search_var.set("")
                atualizar_lista_contatos()

    botao_frame = ttk.Frame(frame)
    botao_frame.pack(fill="x", pady=5)

    ttk.Button(botao_frame, text="Criar Novo Grupo", bootstyle="primary", command=lambda: criar_janela_novo_grupo(atualizar_menu)).pack(side="left", padx=5)
    ttk.Button(botao_frame, text="Remover Grupo Selecionado", bootstyle="danger-outline", command=remover_grupo).pack(side="left", padx=5)

    # Assunto
    ttk.Label(frame, text="Assunto:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
    assunto_entry = ttk.Entry(frame)
    assunto_entry.pack(fill="x", pady=2)

    # Imagem inline
    ttk.Button(frame, text="Selecionar Imagem (Banner)", command=selecionar_imagem_inline).pack(pady=5)

    # Mensagem
    ttk.Label(frame, text="Mensagem (use {nome} para personalizar):", font=("Segoe UI", 10, "bold")).pack(anchor="w")
    mensagem_text = tk.Text(frame, height=8)
    mensagem_text.pack(fill="x", pady=5)
    ttk.Button(frame, text="Salvar como Modelo", command=lambda: salvar_template(simpledialog.askstring("Salvar Modelo", "Nome do modelo:"), mensagem_text.get("1.0", tk.END))).pack(pady=2)
    ttk.Button(frame, text="Carregar Modelo", command=lambda: carregar_template(mensagem_text)).pack(pady=2)

    # E-mail individual
    ttk.Label(frame, text="E-mail individual (opcional):").pack(anchor="w")
    email_individual_entry = ttk.Entry(frame)
    email_individual_entry.pack(fill="x", pady=2)

    # WhatsApp
    ttk.Label(frame, text="Número WhatsApp da empresa (ex: 5511999999999):").pack(anchor="w")
    whatsapp_entry = ttk.Entry(frame)
    whatsapp_entry.pack(fill="x", pady=2)

    # Anexos
    anexos_listbox = tk.Listbox(frame, height=4)
    anexos_listbox.pack(fill="x")
    ttk.Button(frame, text="Adicionar Anexo", command=lambda: selecionar_anexo(anexos_listbox)).pack(pady=2)
    ttk.Button(frame, text="Remover Anexo", command=lambda: remover_anexo(anexos_listbox)).pack(pady=2)


    # Agendamento
    ttk.Label(frame, text="Agendar envio (HH:MM):").pack(anchor="w")
    horario_entry = ttk.Entry(frame)
    horario_entry.pack(fill="x", pady=2)

    ttk.Button(frame, text="Enviar Agora", bootstyle="success", command=lambda: enviar_emails(
        grupos_var.get(),
        assunto_entry.get(),
        mensagem_text.get("1.0", tk.END),
        anexos.copy(),
        email_individual_entry.get().strip(),
        whatsapp_entry.get().strip()
    )).pack(pady=5)

    ttk.Button(frame, text="Agendar Envio", bootstyle="warning-outline", command=lambda: agendar_envio(
        grupos_var.get(),
        assunto_entry.get(),
        mensagem_text.get("1.0", tk.END),
        horario_entry.get()
    )).pack(pady=5)

    ttk.Separator(frame).pack(pady=10, fill="x")

    # Criar novo grupo
    ttk.Label(frame, text="Criar Novo Grupo:", font=("Segoe UI", 10, "bold")).pack(anchor="w")
    grupo_nome_entry = ttk.Entry(frame)
    grupo_nome_entry.pack(fill="x", pady=2)
    grupo_contatos_text = tk.Text(frame, height=5)
    grupo_contatos_text.pack(fill="x")
    ttk.Button(frame, text="Salvar Grupo", bootstyle="primary", command=lambda: salvar_novo_grupo(grupo_nome_entry, grupo_contatos_text, atualizar_menu)).pack(pady=5)


def criar_janela_novo_grupo(atualizar_menu):
    nova = tk.Toplevel()
    nova.title("Criar Novo Grupo")
    nova.geometry("400x300")
    nova.grab_set()

    ttk.Label(nova, text="Nome do Grupo:").pack(pady=5)
    nome_entry = ttk.Entry(nova)
    nome_entry.pack(fill="x", padx=10)

    ttk.Label(nova, text="Contatos (um por linha):").pack(pady=5)
    contatos_text = tk.Text(nova, height=8)
    contatos_text.pack(fill="both", padx=10, pady=5, expand=True)

    ttk.Button(
        nova,
        text="Salvar Grupo",
        bootstyle="success",
        command=lambda: [
            salvar_novo_grupo(nome_entry, contatos_text, atualizar_menu),
            nova.destroy()
        ]
    ).pack(pady=10)

# ---------------- INICIALIZAÇÃO ----------------
def iniciar_app():
    root = Window(themename="superhero")
    root.geometry("1000x600")
    root.withdraw()  # Oculta janela principal inicialmente

    def apos_splash():
        tela_login(root)
        if email_remetente and senha_remetente:
            root.deiconify()
            iniciar_interface(root)
        else:
            root.destroy()

    splash_screen(root, apos_splash)
    root.mainloop()

if __name__ == "__main__":
    iniciar_app()