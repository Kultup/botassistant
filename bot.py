import os
import sys
import git
import subprocess
import logging
import ctypes
import platform
import psutil
import pyautogui
import tkinter as tk
from threading import Thread
from youtubesearchpython import VideosSearch
import yt_dlp
import uuid
import telebot
from datetime import datetime
from PIL import Image, ImageDraw
import pystray
import time  # Импорт модуля time

# Глобальные переменные
last_message_id = None
last_chat_id = None
icon = None  # Иконка для трея

# Путь до GIF-анимации загрузки
LOADING_GIF_PATH = "C:\\Users\\dpytlyk-da\\Desktop\\Bot-aas\\loading.gif"
LOADING_GIF_FRAMES = 60  # Укажите количество кадров в вашем GIF

# Конфигурационные значения напрямую в коде
TELEGRAM_BOT_TOKEN = "7410403471:AAGRMOkcmy3wz4IsRtfSBy7VQoN0QSfVeJM"
YOUTUBE_API_KEY = "AIzaSyAFazoR1V_RvUIqK2YD7ORqTYsmYReSp6g"
GOOGLE_CSE_API_KEY = "AIzaSyAFazoR1V_RvUIqK2YD7ORqTYsmYReSp6g"
GOOGLE_CSE_CX = "b537f9e6ff4ac45cb"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Проверка прав администратора
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except AttributeError:  # Обработка случая, если это не Windows
        return False

# Если требуется выполнить действие с правами администратора
def run_as_admin(action):
    if is_admin():
        action()
    else:
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, ' '.join(sys.argv), None, 1)
            sys.exit()
        except:
            print("Не удалось получить права администратора. Запустите скрипт с правами администратора вручную.")

# Создаем уникальные пути для каждого пользователя
user_folder = os.path.join(os.getenv('APPDATA'), 'Assistant', f"{os.getenv('USERNAME')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
log_file = os.path.join(user_folder, 'bot.log')
mac_address_file = os.path.join(user_folder, 'mac_address.txt')

# Создаем директорию для логов и конфигураций, если ее нет
if not os.path.exists(user_folder):
    os.makedirs(user_folder)

# Логирование
logging.basicConfig(
    filename=log_file, 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    encoding='utf-8'
)

# Функция для получения MAC-адреса
def get_mac_address():
    return ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2*6, 2)][::-1])

# Проверка привязки к MAC-адресу
def check_mac_address():
    current_mac = get_mac_address()
    if os.path.exists(mac_address_file):
        with open(mac_address_file, 'r') as f:
            saved_mac = f.read().strip()
            if current_mac != saved_mac:
                print(f"⚠️ MAC-адрес был изменен с {saved_mac} на {current_mac}. Обновляю привязку.")
                with open(mac_address_file, 'w') as f:
                    f.write(current_mac)
                logging.info(f"Привязка обновлена. Новый MAC-адрес: {current_mac}")
    else:
        # Если файла нет, сохраняем текущий MAC-адрес
        with open(mac_address_file, 'w') as f:
            f.write(current_mac)
        print(f"Привязка к ПК выполнена. MAC-адрес: {current_mac}")
        logging.info(f"Привязка выполнена. MAC-адрес: {current_mac}")

# Проверка на привязку к MAC-адресу
check_mac_address()

# Путь до ffmpeg
FFMPEG_PATH = 'C:/ffmpeg/bin/ffmpeg.exe'

# Получение пути до папки "Музыка с бота" на рабочем столе
def get_music_folder():
    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    music_folder = os.path.join(desktop, "Музыка с бота")
    if not os.path.exists(music_folder):
        os.makedirs(music_folder)
    return music_folder

def send_or_edit_message(chat_id, text, message_id=None, reply_markup=None):
    try:
        if message_id is None:
            message = bot.send_message(chat_id, text, reply_markup=reply_markup)
            return message.message_id
        else:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup)
            return message_id
    except Exception as e:
        logging.error(f"Ошибка при редактировании сообщения: {str(e)}")
        return None

def download_video_1080p(message):
    global last_message_id, last_chat_id
    url = message.text
    chat_id = message.chat.id
    last_chat_id = chat_id  # Сохраняем ID чата для дальнейшего использования

    try:
        send_loading_gif(chat_id)  # Отправляем GIF

        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best',
            'outtmpl': os.path.join(get_music_folder(), '%(title)s.%(ext)s'),
            'retries': 5,
            'noplaylist': True,  # Загрузить только одно видео, а не плейлист
            'merge_output_format': 'mp4',  # Если FFmpeg установлен, эта строка будет полезна
            'ffmpeg_location': FFMPEG_PATH,  # Указываем путь до ffmpeg
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        bot.send_message(chat_id, "🎉 Видео успешно загружено!")
    except Exception as e:
        logging.error(f"Ошибка при загрузке видео: {str(e)}")
        bot.send_message(chat_id, f"❌ Ошибка при загрузке видео: {str(e)}")
    finally:
        bot.send_message(chat_id, "Выберите действие:", reply_markup=get_main_buttons())

def download_audio_from_link(message):
    global last_message_id
    url = message.text
    chat_id = message.chat.id

    try:
        send_loading_gif(chat_id)  # Отправляем GIF

        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/best',
            'outtmpl': os.path.join(get_music_folder(), '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffmpeg_location': FFMPEG_PATH,  # Указываем путь до ffmpeg
            'nopostoverwrites': False,  # Разрешить перезапись существующих файлов
            'noplaylist': True  # Загрузить только одно видео, а не плейлист
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            mp3_file = ydl.prepare_filename(info_dict).replace('.webm', '.mp3')

        bot.send_message(chat_id, f'🎉 Музыка успешно загружена: {mp3_file}')
    except Exception as e:
        logging.error(f"Ошибка при загрузке музыки: {str(e)}")
        bot.send_message(chat_id, f'❌ Ошибка при загрузке музыки: {str(e)}')
    finally:
        bot.send_message(chat_id, "Выберите действие:", reply_markup=get_main_buttons())

def send_loading_gif(chat_id):
    with open(LOADING_GIF_PATH, 'rb') as gif_file:
        message = bot.send_animation(chat_id, gif_file)
    return message.message_id

def get_main_buttons():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🎵 Відтворити музику", callback_data='play_music'),
        telebot.types.InlineKeyboardButton("🎥 Відтворити відео", callback_data='play_video')
    )
    markup.add(
        telebot.types.InlineKeyboardButton("⏸️ Пауза", callback_data='pause_media'),
        telebot.types.InlineKeyboardButton("▶️ Продовжити", callback_data='resume_media')
    )
    markup.add(
        telebot.types.InlineKeyboardButton("🔊 Регулювання звуку", callback_data='volume_control'),
        telebot.types.InlineKeyboardButton("💻 Інформація про ПК", callback_data='pc_info'),
        telebot.types.InlineKeyboardButton("🔋 Перегляд батареї", callback_data='battery_info')
    )
    markup.add(
        telebot.types.InlineKeyboardButton("🌐 Відкрити Chrome", callback_data='open_chrome'),
        telebot.types.InlineKeyboardButton("❌ Закрити Chrome", callback_data='close_chrome')
    )
    markup.add(
        telebot.types.InlineKeyboardButton("🔄 Перезавантаження", callback_data='restart'),
        telebot.types.InlineKeyboardButton("🛑 Вимкнення", callback_data='shutdown'),
        telebot.types.InlineKeyboardButton("💤 Сплячий режим", callback_data='sleep'),
        telebot.types.InlineKeyboardButton("⏲️ Таймер на вимкнення", callback_data='shutdown_timer')
    )
    markup.add(
        telebot.types.InlineKeyboardButton("⬇️ Завантажити музику", callback_data='download_music'),
        telebot.types.InlineKeyboardButton("🎥 Завантажити відео (1080p)", callback_data='download_video_1080p'),
        telebot.types.InlineKeyboardButton("🎵 Завантажити музику (MP3)", callback_data='download_audio')
    )
    markup.add(
        telebot.types.InlineKeyboardButton("🔄 Обновити бота", callback_data='update_bot'),  # Кнопка для обновления
        telebot.types.InlineKeyboardButton("🛑 Зупинити бота", callback_data='stop_bot')
    )
    return markup

# Відтворення музики
def play_music(message):
    search_query = message.text
    videos_search = VideosSearch(search_query, limit=1)
    result = videos_search.result()

    if len(result['result']) > 0:
        video_link = f"https://www.youtube.com/watch?v={result['result'][0]['id']}"
        bot.send_message(message.chat.id, f"🎵 Знайдено: {result['result'][0]['title']}\n{video_link}")
        logging.info(f"Відтворення музики: {video_link}")
        open_in_chrome(video_link)
    else:
        bot.send_message(message.chat.id, "❌ Музику не знайдено.")
        logging.info(f"Музику за запитом '{search_query}' не знайдено.")

# Відтворення відео
def play_video(message):
    search_query = message.text
    videos_search = VideosSearch(search_query, limit=1)
    result = videos_search.result()

    if len(result['result']) > 0:
        video_link = f"https://www.youtube.com/watch?v={result['result'][0]['id']}"
        bot.send_message(message.chat.id, f"🎥 Знайдено: {result['result'][0]['title']}\n{video_link}")
        logging.info(f"Відтворення відео: {video_link}")
        open_in_chrome(video_link)
    else:
        bot.send_message(message.chat.id, "❌ Відео не знайдено.")
        logging.info(f"Відео за запитом '{search_query}' не знайдено.")

# Відкрити в Chrome
def open_in_chrome(url):
    subprocess.run(["start", "chrome", url], shell=True)

# Обробник для інлайн-кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_query_handler(call):
    action = call.data
    logging.info(f"Викликана операція: {action}")

    if action == 'play_music':
        msg = bot.send_message(call.message.chat.id, "🎵 Введіть назву музики:")
        bot.register_next_step_handler(msg, play_music)
    elif action == 'play_video':
        msg = bot.send_message(call.message.chat.id, "🎥 Введіть назву відео:")
        bot.register_next_step_handler(msg, play_video)
    elif action == 'pause_media':
        pyautogui.press('playpause')
        bot.send_message(call.message.chat.id, "⏸️ Відтворення призупинено.")
    elif action == 'resume_media':
        pyautogui.press('playpause')
        bot.send_message(call.message.chat.id, "▶️ Відтворення продовжено.")
    elif action == 'volume_control':
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("🔊 Збільшити гучність", callback_data='volume_up_10'),
            telebot.types.InlineKeyboardButton("🔉 Зменшити гучність", callback_data='volume_down_10'),
            telebot.types.InlineKeyboardButton("🔇 Вимкнути звук", callback_data='mute')
        )
        bot.send_message(call.message.chat.id, "🔊 Оберіть дію для регулювання звуку:", reply_markup=markup)
    elif action == 'pc_info':
        send_pc_info(call.message)
    elif action == 'battery_info':
        send_battery_info(call.message)
    elif action == 'open_chrome':
        open_chrome(call.message)
    elif action == 'close_chrome':
        close_chrome(call.message)
    elif action == 'restart':
        restart_computer(call.message)
    elif action == 'shutdown':
        shutdown_computer(call.message)
    elif action == 'sleep':
        sleep_computer(call.message)
    elif action == 'shutdown_timer':
        msg = bot.send_message(call.message.chat.id, "⏲️ Введіть час у секундах до вимкнення:")
        bot.register_next_step_handler(msg, set_shutdown_timer)
    elif action == 'stop_bot':
        stop_bot(call.message)
    elif action == 'download_music':
        download_audio_from_link(call.message)
    elif action == 'download_video_1080p':
        msg = bot.send_message(call.message.chat.id, "🎥 Введіть посилання на відео для завантаження (1080p):")
        bot.register_next_step_handler(msg, download_video_1080p)
    elif action == 'download_audio':
        msg = bot.send_message(call.message.chat.id, "🎵 Введіть посилання на музику для завантаження (MP3):")
        bot.register_next_step_handler(msg, download_audio_from_link)
    elif action in ['volume_up_10', 'volume_down_10', 'mute']:
        adjust_volume(call.message, action)
    elif action == 'update_bot':  # Обработка обновления бота
        bot.send_message(call.message.chat.id, "🔄 Обновление началось...")
        Thread(target=update_bot, args=(call.message.chat.id,)).start()

# Регулювання звуку
def adjust_volume(message, action):
    logging.info(f"Регулювання звуку: {action}")
    if action == 'volume_up_10':
        for _ in range(10):
            pyautogui.press('volumeup')
        bot.send_message(message.chat.id, "🔊 Гучність збільшено на 10.")
    elif action == 'volume_down_10':
        for _ in range(10):
            pyautogui.press('volumedown')
        bot.send_message(message.chat.id, "🔉 Гучність зменшено на 10.")
    elif action == 'mute':
        pyautogui.press('volumemute')
        bot.send_message(message.chat.id, "🔇 Звук вимкнено.")
    bot.send_message(message.chat.id, "Оберіть дію:", reply_markup=get_main_buttons())

# Інформація про ПК
def send_pc_info(message):
    uname = platform.uname()
    boot_time = psutil.boot_time()
    boot_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(boot_time))
    cpu_info = f"💻 Процесор: {uname.processor}\nКількість ядер: {psutil.cpu_count(logical=False)}\n" \
               f"Кількість потоків: {psutil.cpu_count(logical=True)}"
    mem_info = f"Всього пам'яті: {round(psutil.virtual_memory().total / (1024**3), 2)} GB\n" \
               f"Вільно: {round(psutil.virtual_memory().available / (1024**3), 2)} GB"
    system_info = f"Система: {uname.system} {uname.release}\n" \
                  f"Версія: {uname.version}\n" \
                  f"Ім'я хоста: {uname.node}\n" \
                  f"Час завантаження: {boot_time_str}\n\n" + cpu_info + "\n\n" + mem_info
    bot.send_message(message.chat.id, f"Інформація про систему:\n\n{system_info}")
    logging.info(f"Інформація про систему відправлена: {system_info}")
    bot.send_message(message.chat.id, "Оберіть дію:", reply_markup=get_main_buttons())

# Інформація про батарею
def send_battery_info(message):
    battery = psutil.sensors_battery()
    if battery:
        percent = battery.percent
        plugged = "Так" if battery.power_plugged else "Ні"
        bot.send_message(message.chat.id, f"🔋 Рівень заряду: {percent}%\nПідключено до мережі: {plugged}")
        logging.info(f"Рівень заряду: {percent}%, Підключено до мережі: {plugged}")
    else:
        bot.send_message(message.chat.id, "🔋 Інформація про батарею недоступна.")
        logging.info("Інформація про батарею недоступна.")
    bot.send_message(message.chat.id, "Оберіть дію:", reply_markup=get_main_buttons())

# Відкрити браузер Chrome
def open_chrome(message):
    subprocess.run(["start", "chrome"], shell=True)
    bot.send_message(message.chat.id, "Відкриваю Chrome...")
    logging.info("Відкриваю Chrome")
    bot.send_message(message.chat.id, "Оберіть дію:", reply_markup=get_main_buttons())

# Закрити браузер Chrome
def close_chrome(message):
    subprocess.run(["taskkill", "/IM", "chrome.exe", "/F"], shell=True)
    bot.send_message(message.chat.id, "Закриваю Chrome...")
    logging.info("Закриваю Chrome")
    bot.send_message(message.chat.id, "Оберіть дію:", reply_markup=get_main_buttons())

# Перезавантаження комп'ютера
def restart_computer(message):
    subprocess.run(["shutdown", "/r", "/t", "0"])

# Вимкнення комп'ютера
def shutdown_computer(message):
    subprocess.run(["shutdown", "/s", "/t", "0"])

# Переведення комп'ютера в режим сну
def sleep_computer(message):
    subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "Sleep"])

# Встановлення таймера на вимкнення
def set_shutdown_timer(message):
    time_in_seconds = message.text
    if time_in_seconds.isdigit():
        bot.send_message(message.chat.id, f"⏲️ Комп'ютер буде вимкнено через {time_in_seconds} секунд.")
        subprocess.run(["shutdown", "/s", "/t", time_in_seconds])
        logging.info(f"Таймер на вимкнення встановлено: {time_in_seconds} секунд")
    else:
        bot.send_message(message.chat.id, "⏲️ Введіть коректне число.")
        logging.warning(f"Некоректне значення для таймера: {time_in_seconds}")

# Зупинка бота
def stop_bot(message):
    bot.send_message(message.chat.id, "🛑 Зупинка бота")
    stop_bot_process()

def stop_bot_process():
    bot.stop_polling()
    if icon:
        icon.stop()
    logging.info("Бот зупинений.")
    sys.exit()

# Моніторинг батареї та сповіщення
def monitor_system():
    global last_message_id
    while True:
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            if percent <= 20 and not battery.power_plugged:
                if last_chat_id:
                    bot.send_message(last_chat_id, f"⚠️ Низький рівень заряду батареї: {percent}%")
                logging.warning(f"Низький рівень заряду батареї: {percent}%")
        time.sleep(600)  # Перевірка кожні 10 хвилин

# GUI для управління ботом
def create_gui():
    global root
    root = tk.Tk()
    root.title(f"Управління Telegram ботом")
    root.geometry("300x400")

    # Измененный фон окна
    root.configure(bg="#2e3440")  # Темно-серый фон

    # Новый стиль для кнопок
    button_style = {
        "font": ("Helvetica", 12, "bold"),
        "bg": "#33c0d0",  # Светло-голубой цвет кнопок
        "fg": "white",
        "activebackground": "#27733b",  # Темно-синий цвет при нажатии
        "activeforeground": "white",
        "relief": tk.RAISED,
        "bd": 4,
        "highlightthickness": 2,
        "highlightbackground": "#4c566a",  # Цвет обводки кнопок
    }

    # Новый стиль для меток
    label_style = {
        "font": ("Helvetica", 14, "bold"),
        "bg": "#2e3440",  # Соответствие фону окна
        "fg": "#eceff4",  # Светлый текст
    }

    def start_bot():
        logging.info("Запуск бота")
        Thread(target=bot.polling).start()
        Thread(target=monitor_system).start()

    def stop_bot():
        logging.info("Зупинка бота")
        stop_bot_process()

    def check_for_update():
        logging.info("Перевірка наявності оновлення")
        Thread(target=update_bot, args=(last_chat_id,)).start()

    # Создание интерфейса с новыми стилями
    title_label = tk.Label(root, text="Telegram Бот Управління", **label_style)
    title_label.pack(pady=10)

    tk.Button(root, text="Запустити бота", command=start_bot, **button_style).pack(pady=5)
    tk.Button(root, text="Зупинити бота", command=stop_bot, **button_style).pack(pady=5)
    tk.Button(root, text="Перевірити оновлення", command=check_for_update, **button_style).pack(pady=5)

    powered_label = tk.Label(root, text="Powered by Kultup", font=("Helvetica", 10, "italic"), bg="#2e3440", fg="#88c0d0")
    powered_label.pack(side=tk.BOTTOM, pady=10)

    tk.Button(root, text="Вихід", command=stop_bot, **button_style).pack(pady=5)

    root.protocol("WM_DELETE_WINDOW", stop_bot)  # Обработка закрытия окна через крестик

    root.mainloop()


# Функція для створення іконки
def create_image():
    width = 64
    height = 64
    color1 = "black"
    color2 = "white"

    image = Image.new("RGB", (width, height), color1)
    dc = ImageDraw.Draw(image)
    dc.rectangle(
        (width // 2, 0, width, height // 2), fill=color2
    )
    dc.rectangle(
        (0, height // 2, width // 2, height), fill=color2
    )
    return image

# Функція для запуску бота з трея
def start_bot_tray(icon, item):
    Thread(target=bot.polling).start()
    Thread(target=monitor_system).start()

# Функція для зупинки бота і виходу з програми
def stop_bot_tray(icon, item):
    stop_bot_process()

# Функція для створення іконки в системному треї
def setup_tray():
    global icon
    icon = pystray.Icon("Telegram Bot", create_image(), "Telegram Бот Управління", menu=pystray.Menu(
        pystray.MenuItem("Запустити бота", start_bot_tray),
        pystray.MenuItem("Зупинити бота", stop_bot_tray),
        pystray.MenuItem("Вихід", stop_bot_tray)
    ))
    icon.run()

# Обновление бота
def update_bot(chat_id):
    try:
        # Явный путь к репозиторию
        repo_path = r"C:\Users\dpytlyk-da\Desktop\Bot_aas"

        # Отладочный вывод для проверки пути
        print(f"Путь к репозиторию: {repo_path}")
        logging.info(f"Путь к репозиторию: {repo_path}")

        # Проверяем, что папка .git существует в данной директории
        if os.path.exists(os.path.join(repo_path, ".git")):
            print("Папка .git найдена.")
            logging.info("Папка .git найдена.")
            
            # Открываем репозиторий
            repo = git.Repo(repo_path)
            origin = repo.remotes.origin
            
            # Выполняем pull для получения последних изменений
            origin.pull()
            logging.info("Обновление бота завершено успешно.")
            bot.send_message(chat_id, "✅ Бот был обновлен до последней версии.")
        else:
            logging.error("Репозиторий не найден.")
            bot.send_message(chat_id, "❌ Репозиторий не найден.")
            return

        # Перезапуск бота после обновления
        restart_bot()

    except Exception as e:
        logging.error(f"Ошибка при обновлении бота: {str(e)}")
        bot.send_message(chat_id, f"❌ Ошибка при обновлении бота: {str(e)}")

def restart_bot():
    python = sys.executable
    os.execl(python, python, *sys.argv)


# Обробник команди /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    global last_message_id, last_chat_id
    last_chat_id = message.chat.id  # Збереження ідентифікатора чату
    logging.info(f"Користувач {message.from_user.username} ({message.from_user.id}) використав команду /start")
    
    welcome_message = (
        "Привіт! Я ваш асистент-бот. Я можу допомогти вам з різними завданнями, "
        "такими як відтворення музики, управління комп'ютером та багато іншого.\n"
        "Використовуйте меню нижче, щоб почати!"
    )
    
    bot.send_message(message.chat.id, welcome_message)
    bot.send_message(message.chat.id, "Оберіть дію:", reply_markup=get_main_buttons())

# Запуск GUI та Telegram клієнта
if __name__ == "__main__":
    Thread(target=create_gui).start()
    setup_tray()
