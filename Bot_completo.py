import sqlite3
import time
import json
from pynput import keyboard, mouse
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import winsound
import pyautogui
from ttkthemes import ThemedTk

# Variáveis globais
is_running = False
bot_paused = False
coordinates_ins = []
coordinates_home = []
start_time = None
ins_travel_times = []
image_path = 'letra_o.png'

# Função para criar o banco de dados (se não existir)
def criar_banco_de_dados():
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL)''')
    conn.commit()
    conn.close()

# Função para autenticar o usuário
def autenticar_usuario(usuario, senha):
    conn = sqlite3.connect('usuarios.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE username = ? AND password = ?", (usuario, senha))
    resultado = cursor.fetchone()
    conn.close()
    return resultado

# Funções do bot
def save_coordinates_to_file():
    filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if filepath:
        with open(filepath, 'w') as f:
            json.dump({
                'ins': coordinates_ins,
                'home': coordinates_home,
                'travel_times': ins_travel_times
            }, f)
        messagebox.showinfo("Salvar Coordenadas", "Coordenadas e tempos salvos com sucesso!")

def load_coordinates_from_file():
    global coordinates_ins, coordinates_home, ins_travel_times
    filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if filepath:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                coordinates_ins = data.get('ins', [])
                coordinates_home = data.get('home', [])
                ins_travel_times = data.get('travel_times', [0] * len(coordinates_ins))
            messagebox.showinfo("Carregar Coordenadas", "Coordenadas e tempos carregados com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar coordenadas: {e}")

def save_coordinates_ins():
    global coordinates_ins
    coordinates_ins.append(mouse_controller.position)
    print(f"Coordenadas INS salvas: {coordinates_ins[-1]}")

def save_coordinates_home():
    global coordinates_home
    coordinates_home.append(mouse_controller.position)
    print(f"Coordenadas HOME salvas: {coordinates_home[-1]}")

def clear_coordinates():
    global coordinates_ins, coordinates_home, ins_travel_times
    coordinates_ins.clear()
    coordinates_home.clear()
    ins_travel_times.clear()
    messagebox.showinfo("Zerar Coordenadas", "As coordenadas foram zeradas.")

def start_timer():
    global start_time
    start_time = time.time()

def stop_timer():
    elapsed_time = time.time() - start_time
    print(f"Tempo registrado: {elapsed_time:.2f} segundos")
    return elapsed_time

def check_pause():
    global bot_paused
    while bot_paused:
        time.sleep(0.1)  # Empty loop while the bot is paused

def continue_bot():
    global bot_paused
    bot_paused = False
    print("Bot continued.")

def collect_resources(home_coordinate):
    global bot_paused
    check_pause()
    time.sleep(0.1)
    mouse_controller.position = home_coordinate
    time.sleep(0.4)
    print(f"Coletando recursos na coordenada HOME: {home_coordinate}...")
    keyboard_controller.press('c')
    keyboard_controller.release('c')
    try:
        time.sleep(0.3)  # Ajuste o tempo se necessário
        search_region = (692, 119, 642, 224)  # Exemplo de valores, ajuste conforme necessário
        print("Verificando a imagem na tela na região definida...")
        location = pyautogui.locateOnScreen(image_path, region=search_region, confidence=0.8)
        if location is not None:
            print("Imagem encontrada na tela.")
            tocar_alarme()
            time.sleep(12)  # Pausa de 10 segundos após encontrar a imagem
        else:
            print("Imagem não encontrada, continuando a execução.")
    except Exception as e:
        print(f"Ocorreu um erro ao verificar a imagem: {e}")
    time.sleep(2.6)
    print("Recursos coletados.")
    keyboard_controller.press('v')
    keyboard_controller.release('v')

def move_to_ins(ins_coordinate, travel_time):
    global bot_paused
    check_pause()  # Verifica se está pausado antes de prosseguir
    time.sleep(0.1)
    mouse_controller.position = ins_coordinate
    time.sleep(1)
    print(f"Movendo para a coordenada INS: {ins_coordinate}...")
    mouse_controller.click(mouse.Button.left)
    print(f"Aguardando {travel_time:.2f} segundos para locomoção.")
    time.sleep(travel_time)
    keyboard_controller.press('v')
    keyboard_controller.release('v')
    keyboard_controller.press('f')
    keyboard_controller.release('f')

def tocar_alarme():
    frequency = 2500  # Hertz
    duration = 1000   # 1 segundo
    winsound.Beep(frequency, duration)

def bot_loop():
    global is_running, ins_travel_times
    if not coordinates_ins or not coordinates_home:
        messagebox.showwarning("Iniciar Bot", "É necessário salvar coordenadas INS e HOME antes de iniciar.")
        return

    while is_running:
        for i, (ins_coordinate, home_coordinate) in enumerate(zip(coordinates_ins, coordinates_home)):
            if not is_running:
                print("Bot interrompido.")
                break
            time.sleep(0.1)        
            check_pause()  # Verifica se está pausado antes de prosseguir

            start_timer()
            move_to_ins(ins_coordinate, ins_travel_times[i])
            travel_time = stop_timer()
            ins_travel_times.append(travel_time)
            collect_resources(home_coordinate)

        print("Reiniciando o ciclo de coleta...")

def stop_bot():
    global is_running
    is_running = False
    print("Bot parado.")

def on_press(key):
    global bot_paused, is_running  # Adiciona is_running aqui para usar na função
    try:
        # Iniciar o bot ao pressionar Delete
        if key == keyboard.Key.delete:
            if not is_running:
                print("Iniciando o bot...")
                is_running = True
                bot_loop()
            else:
                print("O bot já está rodando.")

        # Parar o bot ao pressionar End
        elif key == keyboard.Key.end:
            stop_bot()
            return False  # Para o listener

        # Iniciar o cronômetro ao pressionar Page Up
        elif key == keyboard.Key.page_up:
            start_timer()
            print("Cronômetro iniciado.")

        # Parar o cronômetro e salvar tempo ao pressionar Page Down
        elif key == keyboard.Key.page_down:
            travel_time = stop_timer()
            ins_travel_times.append(travel_time)
            print(f"Tempo de locomoção salvo: {travel_time:.2f} segundos")

        # Salvar coordenadas INS ao pressionar Insert
        elif key == keyboard.Key.insert:
            save_coordinates_ins()

        # Salvar coordenadas HOME ao pressionar Home
        elif key == keyboard.Key.home:
            save_coordinates_home()
        
        # Pausar bot ao pressionar Pause
        elif key == keyboard.Key.pause:
            global bot_paused
            bot_paused = not bot_paused
            if bot_paused:
                print("Bot pausado.")
            else:
                print("Bot continuado.")

    except Exception as e:
        print(f"Erro: {e}")

# Configuração dos listeners
mouse_controller = mouse.Controller()
keyboard_controller = keyboard.Controller()

# Função para centralizar a janela
def centralizar_janela(janela, largura, altura):
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    pos_x = (largura_tela // 2) - (largura // 2)
    pos_y = (altura_tela // 2) - (altura // 2)
    janela.geometry(f'{largura}x{altura}+{pos_x}+{pos_y}')

# Interface gráfica para login
def create_login_gui():
    global janela
    janela = tk.Tk()
    janela.title("Login do Bot")

    # Tamanho da janela
    LARGURA_JANELA = 300
    ALTURA_JANELA = 200

    # Centraliza a janela na tela
    centralizar_janela(janela, LARGURA_JANELA, ALTURA_JANELA)

    # Carregar imagem de fundo
    img = Image.open('gengar_bot.png')
    img = img.resize((LARGURA_JANELA, ALTURA_JANELA), Image.LANCZOS)
    img_tk = ImageTk.PhotoImage (img)
    bg_label = tk.Label(janela, image=img_tk)
    bg_label.place(relwidth=1, relheight=1)

    # Widgets de entrada
    tk.Label(janela, text="Usuário:").pack(pady=10)
    entry_usuario = tk.Entry(janela)
    entry_usuario.pack(pady=5)

    tk.Label(janela, text="Senha:").pack(pady=10)
    entry_senha = tk.Entry(janela, show="*")
    entry_senha.pack(pady=5)

    def login():
        usuario = entry_usuario.get()
        senha = entry_senha.get()
        if autenticar_usuario(usuario, senha):
            janela.destroy()
            create_bot_gui()
        else:
            messagebox.showerror("Erro", "Usuário ou senha inválidos.")

    # Botão de Login
    login_button = tk.Button(janela, text="Login", command=login)
    login_button.pack(pady=20)

    # Acionar login ao pressionar Enter
    janela.bind('<Return>', lambda event: login())

    janela.mainloop()

# Interface gráfica do bot

def create_bot_gui():
    global bot_window
    bot_window = tk.Tk()
    bot_window.title("Bot de Coleta")

    # Mantém a janela sempre no topo
    bot_window.attributes('-topmost', True)

    # Tamanho da janela
    LARGURA_JANELA_BOT = 300
    ALTURA_JANELA_BOT = 320

    # Centraliza a janela na tela
    centralizar_janela(bot_window, LARGURA_JANELA_BOT, ALTURA_JANELA_BOT)

    # Carregar imagem de fundo
    img_bg = Image.open('interface_bot.png')
    img_bg = img_bg.resize((LARGURA_JANELA_BOT, ALTURA_JANELA_BOT), Image.LANCZOS)
    img_bg_tk = ImageTk.PhotoImage(img_bg)
    bg_label = tk.Label(bot_window, image=img_bg_tk)
    bg_label.place(relwidth=1, relheight=1)

    # Estilo do ttk
    style = ttk.Style()
    style.theme_use('clam')  

    # Adicionando botões com estilo ttk
    ttk.Button(bot_window, text="Continuar", command=continue_bot).pack(pady=10)
    ttk.Button(bot_window, text="Pausar", command=lambda: pause_bot()).pack(pady=10)
    ttk.Button(bot_window, text="Salvar Coordenadas", command=save_coordinates_to_file).pack(pady=10)
    ttk.Button(bot_window, text="Carregar Coordenadas", command=load_coordinates_from_file).pack(pady=10)
    ttk.Button(bot_window, text="Zerar Coordenadas", command=clear_coordinates).pack(pady=10)
    ttk.Button(bot_window, text="Instruções", command=show_instructions).pack(pady=10)

    # Configuração de um estilo para a janela
    bot_window.configure(bg='#ffffff')  # Cor de fundo da janela

    # Evento para mover a janela
    def move_window(event):
        x = bot_window.winfo_x() + event.x
        y = bot_window.winfo_y() + event.y
        bot_window.geometry(f"+{x}+{y}")

    # Adicionando o evento de clique e arraste
    bg_label.bind("<ButtonPress-1>", lambda event: bg_label.bind("<B1-Motion>", move_window))
    bg_label.bind("<ButtonRelease-1>", lambda event: bg_label.unbind("<B1-Motion>"))

    # Iniciar o listener de teclado
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    bot_window.mainloop()

def pause_bot():
    global bot_paused
    bot_paused = True
    print("Bot pausado.")
    
# Função para exibir instruções
def show_instructions():
    instructions = (
        "Instruções de Uso:\n"
        "1. Salve as coordenadas INS e HOME antes de iniciar o bot.\n"
        "2. Pressione Delete para iniciar o bot.\n"
        "3. Pressione End para parar o bot.\n"
        "4. Use as teclas Page Up e Page Down para registrar os tempos de locomoção.\n"
        "5. Pressione Insert para salvar coordenadas INS e Home para salvar coordenadas HOME.\n"
        "6. Pressione Pause para pausar o bot.\n"
        "7. As coordenadas e tempos podem ser salvos e carregados em arquivos JSON."
    )
    messagebox.showinfo("Instruções", instructions)

# Cria o banco de dados e a interface de login
criar_banco_de_dados()
create_login_gui()

#esse é o bot certo