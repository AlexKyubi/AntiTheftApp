import io
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import os
import sys
from screeninfo import get_monitors
import psutil
import re
import time
import threading
import comtypes
import ctypes
import subprocess
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
import winreg



os.system("chcp 65001")  # Устанавливает кодировку UTF-8 для консоли
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# Путь для хранения флагов и данных
REG_PATH = r"Software\AntiTheftApp"  # Путь в реестре для хранения данных
# Пароль администратора и команда отключения
ADMIN_PASSWORD = "Alexkyubi"
STOP_COMMAND = "stop_alarm"
startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
file_path = os.path.join(startup_folder, 'main.exe')

# Константы Windows
SW_HIDE = 0
SW_SHOW = 5
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001


# Глобальная переменная для контроля тревоги
alarm_active = False
power_restored = True  # Флаг для определения состояния питания

# Установка состояния для предотвращения спящего режима
def prevent_sleep_mode():
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)


# Скрыть консоль
def hide_console():
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), SW_HIDE)


# Показать консоль
def show_console():
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    ctypes.windll.user32.ShowWindow(hwnd, SW_SHOW)


# Сохранение времени закрытия
def save_close_time_to_registry(close_time):
    try:
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, REG_PATH)
        winreg.SetValueEx(key, "TIME_CLOSE", 0, winreg.REG_SZ, close_time)
        winreg.CloseKey(key)
        print(f"[ИНФО] Время закрытия магазина сохранено: {close_time}")
    except Exception as e:
        print(f"[ОШИБКА] Не удалось сохранить время в реестр: {e}")


# Сохранение пароля
def save_password(password):
    try:
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, REG_PATH)
        winreg.SetValueEx(key, "Password", 0, winreg.REG_SZ, password)
        winreg.CloseKey(key)
        print("[ИНФО] Пароль сохранён в реестре.")
    except Exception as e:
        print(f"[ОШИБКА] Не удалось сохранить пароль в реестр: {e}")


# Удаление пароля
def delete_password():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_PATH, 0, winreg.KEY_WRITE)
        winreg.DeleteValue(key, "Password")
        winreg.CloseKey(key)
        print("[ИНФО] Пароль успешно удалён из реестра.")
    except FileNotFoundError:
        print("[ИНФО] Пароль в реестре не найден. Удаление не требуется.")
    except Exception as e:
        print(f"[ОШИБКА] Не удалось удалить пароль из реестра: {e}")


# Чтение времени закрытия из реестра
def read_close_time_from_registry():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_PATH)
        close_time, _ = winreg.QueryValueEx(key, "TIME_CLOSE")
        winreg.CloseKey(key)
        return close_time
    except Exception as e:
        pass
        return "20:00"


# Чтение пароля из реестра
def read_password_from_registry():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REG_PATH)
        password, _ = winreg.QueryValueEx(key, "Password")
        winreg.CloseKey(key)
        return password
    except Exception as e:
        pass
        return None



def check_password(password):
    stored_password = read_password_from_registry()
    
    # Если введённый пароль совпадает с паролем в реестре или с резервным
    if password == stored_password or password == ADMIN_PASSWORD:
        print("[ИНФО] Тревога отключена администратором.")
        return True
    
    print("[ОШИБКА] Неверный пароль!")
    return False


# Проверка команды остановки
def check_stop_command(password):
    global alarm_active
    if password == STOP_COMMAND:
        # Основная логика функции
        print("[ИНФО] Программа завершена принудительно.")
        return True
        
   
        
        


# Установка "Ничего не делать" при закрытии крышки и нажатии кнопки питания
def set_lid_close_action():
    try:
        subprocess.run(
            [
                "powercfg", "-setdcvalueindex", "scheme_current", "SUB_BUTTONS",
                "LIDACTION", "0"
            ],
            check=True
        )
        subprocess.run(
            [
                "powercfg", "-setacvalueindex", "scheme_current", "SUB_BUTTONS",
                "LIDACTION", "0"
            ],
            check=True
        )
        subprocess.run(
            [
                "powercfg", "-setdcvalueindex", "scheme_current", "SUB_BUTTONS",
                "PBUTTONACTION", "0"
            ],
            check=True
        )
        subprocess.run(
            [
                "powercfg", "-setacvalueindex", "scheme_current", "SUB_BUTTONS",
                "PBUTTONACTION", "0"
            ],
            check=True
        )
        subprocess.run(["powercfg", "-setactive", "scheme_current"], check=True)
        print("[ИНФО] Закрытие крышки и кнопки питания успешно отключены.")
    except Exception as e:
        print(f"[ОШИБКА] Не удалось изменить настройки крышки и кнопки питания: {e}")


def disable_device():
    try:
        # Запуск командой для открытия панели звуковых устройств
        subprocess.run('start mmsys.cpl', shell=True)
        print("[ИНФО] Панель звуковых устройств открыта. Щелкните на устройство наушники(HeadSet) правой кнопкой и нажмите Отключить.")

        # Ожидание, пока пользователь не нажмет Enter
        input("[ИНФО] Полсле нажмите Enter, если устройство наушники(HeadSet) отключено.")
        print("[ИНФО] Если вы сделали что-то неправильно, просто закройте окно консоли и программа перезапустится")
        
    except Exception as e:
        print(f"[ОШИБКА] Произошла ошибка: {e}")


# Установка времени системы
def set_system_time():
    """
    Устанавливает системное время. Ожидает ввод только часов и минут в любом формате.
    """
    while True:
        try:
            new_time = input("Введите точное время (часы и минуты) например 9.00: ").strip()
            print("Если вы ввели неправильное время, закойте окно консоли и попробуйте снова.")
            
            # Приведение ввода к числовому формату
            time_match = re.match(r"(\d+)[.,:/\\ ]*(\d{2})?", new_time)
            if not time_match:
                raise ValueError("Неверный формат времени. Попробуйте снова.")

            # Извлечение часов и минут
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2)) if time_match.group(2) else 0

            # Проверка допустимости времени
            if not (0 <= hours < 24) or not (0 <= minutes < 60):
                raise ValueError("Время выходит за пределы допустимого диапазона.")

            # Форматирование времени
            formatted_time = f"{hours:02d}:{minutes:02d}:00"

            # Установка времени через команду
            subprocess.run(["cmd", "/c", f"time {formatted_time}"], check=True)
            print(f"[ИНФО] Время успешно установлено: {formatted_time}")
            
            # Спросим до скольки работает магазин
            store_close_time = input("Введите время закрытия магазина (например 21.00): ").strip()
            print("Если вы ввели неправильное время, закойте окно консоли и попробуйте снова.")
            store_close_time_match = re.match(r"(\d+)[.,:/\\ ]*(\d{2})?", store_close_time)
            
            if store_close_time_match:
                close_hour = int(store_close_time_match.group(1))
                close_minute = int(store_close_time_match.group(2))
                
                # Сохранение времени закрытия в реестр
                save_close_time_to_registry(f"{close_hour:02d}:{close_minute:02d}")
            else:
                print("[ОШИБКА] Неверный формат времени.")
            
            break
        except ValueError as ve:
            print(f"[ОШИБКА] {ve}")
        except Exception as e:
            print(f"[ОШИБКА] Не удалось установить время: {e}")


# Мониторинг питания
def monitor_power():
    global alarm_active, power_restored
    while True:
        # Получаем информацию о батарее
        battery = psutil.sensors_battery()
        if battery and not battery.power_plugged:
            if not alarm_active and power_restored:
                alarm_active = True
                power_restored = False                                
                # Воспроизведение звукового сигнала
                print("[ТРЕВОГА] Питание отключено! Введите пароль для отключения тревоги.")
                threading.Thread(target=alarm_sound, daemon=True).start()

                 # Ожидание ввода пароля через графическое окно
                prompt_password_window()
        elif battery and battery.power_plugged:
            power_restored = True
        time.sleep(3)


# Изменение уровня громкости
class VolumeControl:
    def __init__(self):
        self.devices = AudioUtilities.GetSpeakers()
        self.interface = self.devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = self.interface.QueryInterface(IAudioEndpointVolume)

    def set_volume_max(self):
        """
        Устанавливает максимальную громкость на Windows.
        """
         # Проверяем, включен ли режим "Звук отключен"
        is_muted = self.volume.GetMute()
        if is_muted:
             self.volume.SetMute(0, None)  # Выключаем "Звук отключен"
            

        # Проверяем текущий уровень громкости
        current_volume = self.volume.GetMasterVolumeLevelScalar()
        if current_volume < 1.0:
              self.volume.SetMasterVolumeLevelScalar(1.0, None)  # Устанавливаем максимальную громкость

# Функция для отслеживания изменения уровня громкости
def monitor_volume():
    """
    Постоянно следит за уровнем громкости и при необходимости устанавливает максимум.
    """
    comtypes.CoInitialize()  # Инициализация COM
    volume_control = VolumeControl()
    while True:
        try:
            volume_control.set_volume_max()
            time.sleep(3)  # Проверяем каждые 3 секунды
        except Exception as e:
            print(f"[ОШИБКА] {e}")
            break


# Функция для воспроизведения длительного звукового сигнала
def alarm_sound():
    """
    Воспроизводит сигнал тревоги через системную пищалку (PC Beep).
    Сохраняет функционал увеличения частоты и уменьшения паузы.
    """
    global alarm_active
    initial_frequency = 2800  # Начальная частота (Гц)
    initial_duration = 1000    # Начальная длительность сигнала (мс)
    initial_pause = 500       # Начальная пауза между сигналами (мс)

    while alarm_active:
        frequency = initial_frequency
        duration = initial_duration
        pause = initial_pause

        # Основной цикл на 50 секунд с увеличением частоты и уменьшением паузы
        for elapsed_time in range(50):  # Первые 50 секунд
            if not alarm_active:
                return  # Выход, если тревога отключена

            # Воспроизведение сигнала через PC Beep
            ctypes.windll.kernel32.Beep(frequency, duration)
            time.sleep(pause / 1000.0)  # Переводим паузу в секунды

            # Увеличиваем частоту и уменьшаем паузу для создания напряжения
            frequency += 10
            pause = max(50, pause - 10)  # Минимальная пауза - 50 мс

        # Последние 10 секунд — непрерывный сигнал
        if alarm_active:
            ctypes.windll.kernel32.Beep(frequency, 10000)  # Непрерывный сигнал 10 секунд

        # Сброс параметров
        frequency = initial_frequency
        duration = initial_duration
        pause = initial_pause


# Отключение кнопок завершения работы системы и панели управления
def disable_shutdown_buttons_and_control_panel():
    try:
        # Отключение кнопок завершения работы системы
        key_path_explorer = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer"
        
        # Создаем/открываем реестр для "NoClose"
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path_explorer)
        winreg.SetValueEx(key, "NoClose", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        print("[ИНФО] Отключены кнопки завершения работы системы.")

                       
        # Создаем/открываем реестр для "NoControlPanel"
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path_explorer)
        winreg.SetValueEx(key, "NoControlPanel", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        print("[ИНФО] Панель управления заблокирована.")

        # Создаем/открываем реестр для "NoLogoff"
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path_explorer)
        winreg.SetValueEx(key, "NoLogoff", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
        print("[ИНФО] Кнопка 'Выход из системы' отключена.")
       
       # Отключение UAC (EnableLUA = 0)
        key_path_uac = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path_uac)
        winreg.SetValueEx(key, "EnableLUA", 0, winreg.REG_DWORD, 0)
        winreg.CloseKey(key)
        print("[ИНФО] UAC отключен (EnableLUA = 0).")
                      
        # Путь в реестре для подмены диспетчера задач
        key_path_taskmgr = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\taskmgr.exe"        
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path_taskmgr)        
        # Создаём строковый параметр Debugger с путём к вашей программе
        debugger_path = r"C:\Users\user\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\main.exe"
        winreg.SetValueEx(key, "Debugger", 0, winreg.REG_SZ, debugger_path)        
        winreg.CloseKey(key)        
        print("[ИНФО] Диспетчер задач перенаправлен на вашу программу.")


         # Перезагрузка системы для применения изменений
        print("[ИНФО] Перезагрузка системы для применения изменений.")
        time.sleep(10)
        subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
    
    except PermissionError:
        print("[ОШИБКА] Недостаточно прав для изменения реестра. Запустите программу от имени администратора.")
    except Exception as e:
        print(f"[ОШИБКА] Не удалось выполнить операцию: {e}")

# Восстановление кнопок завершения работы системы и панели управления
def restore_shutdown_buttons_and_control_panel():    
    try:
        # Восстановление параметра "NoClose"
        key_path_explorer = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer"
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path_explorer, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, "NoClose")
            winreg.CloseKey(key)
            print("[ИНФО] Кнопки завершения работы системы восстановлены.")
        except FileNotFoundError:
            print("[ИНФО] Параметр NoClose не найден, пропускаем.")
        except Exception as e:
            print(f"[ОШИБКА] Не удалось восстановить кнопки завершения работы системы: {e}")
        
        # Восстановление параметра "NoControlPanel"
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path_explorer, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, "NoControlPanel")
            winreg.CloseKey(key)
            print("[ИНФО] Панель управления восстановлена.")
        except FileNotFoundError:
            print("[ИНФО] Параметр NoControlPanel не найден, пропускаем.")
        except Exception as e:
            print(f"[ОШИБКА] Не удалось восстановить панель управления: {e}")

        # Удаляем параметр "NoLogoff" из реестра
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path_explorer, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, "NoLogoff")
            winreg.CloseKey(key)
            print("[ИНФО] Кнопка 'Выход из системы' снова включена.")
        except FileNotFoundError:
            print("[ИНФО] Параметр 'NoLogoff' уже отсутствует.")
        except Exception as e:
            print(f"[ОШИБКА] Не удалось включить кнопку 'Выход из системы': {e}")

        try:
            # Включение UAC (EnableLUA = 1)
            key_path_uac = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path_uac)
            winreg.SetValueEx(key, "EnableLUA", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            print("[ИНФО] UAC включен (EnableLUA = 1).")
        except PermissionError:
            print("[ОШИБКА] Недостаточно прав для изменения реестра. Запустите программу от имени администратора.")
        except Exception as e:
            print(f"[ОШИБКА] Не удалось выполнить операцию: {e}")

        # Восстановление диспетчера задач (удаление Debugger)
        key_path_taskmgr = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\taskmgr.exe"
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path_taskmgr, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, "Debugger")
            winreg.CloseKey(key)
            print("[ИНФО] Диспетчер задач восстановлен.")
        except FileNotFoundError:
            print("[ИНФО] Параметр Debugger не найден, пропускаем.")
        except Exception as e:
            print(f"[ОШИБКА] Не удалось восстановить диспетчер задач: {e}")

        # Удаление файла autorun.vbs из автозагрузки
        startup_folder = os.path.join(os.environ.get("ALLUSERSPROFILE"), "Microsoft\\Windows\\Start Menu\\Programs\\Startup")
        autorun_path = os.path.join(startup_folder, "autorun.vbs")
        try:
            os.remove(autorun_path)
            print(f"[ИНФО] Файл '{autorun_path}' успешно удалён из автозагрузки.")
        except FileNotFoundError:
            print(f"[ИНФО] Файл '{autorun_path}' не найден в автозагрузке.")
        except Exception as e:
            print(f"[ОШИБКА] Не удалось удалить файл '{autorun_path}' из автозагрузки: {e}")

        # Создание файла stop_alarm.txt на рабочем столе
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        stop_file_path = os.path.join(desktop_path, "stop_alarm.txt")
        try:
            with open(stop_file_path, "w") as stop_file:
                stop_file.write("Настройки восстановлены.")
            print(f"[ИНФО] Файл '{stop_file_path}' успешно создан.")
        except Exception as e:
            print(f"[ОШИБКА] Не удалось создать файл '{stop_file_path}': {e}")

        delete_password()

        # Перезагрузка системы для применения изменений
        print("[ИНФО] Перезагрузка системы для применения изменений.")
        time.sleep(10)

        subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
    
    except PermissionError:
        print("[ОШИБКА] Недостаточно прав для изменения реестра. Запустите программу от имени администратора.")
    except Exception as e:
        print(f"[ОШИБКА] Не удалось восстановить настройки: {e}")


# Проверка времени и выполнение команды shutdown
def check_time_and_shutdown():
    while True:
        # Получаем текущее время
        current_time = datetime.now().strftime("%H:%M")
        
        # Чтение времени закрытия магазина из реестра
        close_time = read_close_time_from_registry()
        # Если время закрытия установлено, проверяем текущее время
        if close_time:
            # Если текущее время >= времени закрытия, выполняем команду shutdown
            if current_time >= close_time:
                print(f"[ИНФО] Время {current_time} Магазин закрывается. Выполняем команду shutdown.")
                subprocess.run(["shutdown", "/s", "/t", "15"], check=True)

                # Пауза на 1 час после выполнения команды, чтобы не запускать её несколько раз в течение этого времени
                time.sleep(600)  # Задержка в 10 минут
            else:                
                pass
        else:
            print("[ОШИБКА] Время закрытия не установлено.")

        # Пауза на 5 минут перед следующей проверкой
        time.sleep(300)  # Проверяем время каждые 5 минут


# Функция для обработки клика по окну
def on_window_click():
    # Создание окна для уведомления
    message = (
        "******************************************\n"
        "*            АНТИКРАЖНАЯ СИСТЕМА      *\n"
        "******************************************\n\n"
        
        "Разработано талантливыми сотрудниками магазина 22K01.\n\n"
        
        "Компания Sulpak гордится инновационными решениями, которые делают покупки безопасными и удобными.\n\n"
        
        "Все права на данный продукт защищены. Он является исключительной собственностью компании Sulpak.\n"
        "Использование этого продукта без официального разрешения строго запрещено.\n\n"
        
        "Программное обеспечение было создано с целью повышения качества обслуживания клиентов и улучшения уровня защиты.\n\n"
        
        "Мы ценим вашу безопасность и комфорт.\n"
        "*********************************************\n"
    )
    # Создаем всплывающее окно с сообщением
    messagebox.showinfo("Антикражная система", message)


# Создание окна уведомленияыещз
def create_notification_window():
    # Получаем информацию о мониторе
    monitor = get_monitors()[0]
    screen_width = monitor.width
    screen_height = monitor.height   

    # Позиционируем окно в нижнем правом углу экрана, чуть выше панели задач
    x_pos = screen_width - 430  # Позиция окна по оси X (от правого края)
    y_pos = screen_height - 150  # Позиция окна по оси Y (от нижнего края)

    root = tk.Tk()
    root.overrideredirect(True)  # Окно без заголовка
    root.geometry(f"+{x_pos}+{y_pos}")  # Позиция окна в правом нижнем углу
    root.attributes('-topmost', True)  # Окно всегда поверх других окон
    root.after(10, lambda: root.lift())  # Перемещаем окно наверх
    root.attributes('-transparentcolor', 'gray')  # Сделать фон полупрозрачным
    

    # Сделаем окно с полупрозрачным темным фоном
    frame = tk.Frame(root, bg='#333333', bd=0)  # Темно-серый цвет фона
    frame.pack(padx=10, pady=5)  # Уменьшаем отступы по высоте
     # Измененные параметры кнопки
    button = tk.Button(
        frame, 
        text="Система в режиме безопасности.", 
        font=("Arial", 14, "bold"),  # Уменьшаем размер шрифта
        fg="white", 
        bg="#4C4C4C",  # Цвет фона кнопки
        relief="solid",  # Рамка вокруг кнопки
        bd=2,  # Толщина рамки
        padx=20, pady=8,  # Уменьшаем области клика по высоте
        command=lambda event=None: on_window_click(),  # Привязка события нажатия к функции
        activebackground="#555555",  # Цвет фона при наведении
        activeforeground="white",  # Цвет текста при наведении
        highlightbackground="#4C4C4C",  # Цвет рамки
        highlightthickness=0,  # Убираем рамку при нажатии
        width=25, height=1  # Уменьшаем высоту и увеличиваем ширину
    )
    button.pack()      

    # Окно будет всегда сверху, пока программа работает
    root.mainloop()


# Окно для ввода пароля
def prompt_password_window():
    global alarm_active

    # Цикл для повторного запуска окна, если оно закрыто до ввода пароля
    while alarm_active:
        # Создаем окно
        window = tk.Tk()
        window.title("Тревога: Введите пароль")

        # Убираем возможность изменения размера окна
        window.resizable(False, False)

        # Позиционируем окно по центру экрана
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        window_width = 500
        window_height = 200
        position_top = int(screen_height / 2 - window_height / 2)
        position_left = int(screen_width / 2 - window_width / 2)
        window.geometry(f'{window_width}x{window_height}+{position_left}+{position_top}')

        # Убираем кнопки закрытия (окно не будет сворачиваться или закрываться через стандартные кнопки)
        window.protocol("WM_DELETE_WINDOW", lambda: None)  # Запрещаем закрытие через X

        # Окно всегда поверх других окон
        window.attributes('-topmost', True)

        # Добавляем метку с текстом
        label = tk.Label(window, text="Введите пароль для отключения тревоги:")
        label.pack(pady=(10, 5))  # Отступы сверху и снизу

        # Метка для вывода статуса (ошибка или успех)
        status_label = tk.Label(window, text="", fg="red")
        status_label.pack(pady=(5, 10))  # Меньше отступа сверху, чтобы место было для кнопки

        # Поле ввода пароля
        password_entry = tk.Entry(window, show="*")
        password_entry.pack(pady=(5, 10), expand=True)  # Подняли поле ввода, чтобы оно не перекрывало метку

        def on_submit():
            password = password_entry.get().strip()
            global alarm_active

            # Проверка команды остановки
            if check_stop_command(password):
                status_label.config(text="Программа завершена. Восстановление настроек...", fg="blue")
                alarm_active = False
                window.after(2000, window.destroy)  # Закрытие окна через 2 секунды
                restore_shutdown_buttons_and_control_panel()
                return

            # Проверка стандартного пароля
            elif check_password(password):
                status_label.config(text="Тревога отключена. Программа возвращается в скрытый режим.", fg="green")
                alarm_active = False  # Отключаем тревогу
                window.after(2000, window.destroy)  # Закрытие окна через 2 секунды
            else:
                status_label.config(text="Неверный пароль! Попробуйте снова.", fg="red")
                password_entry.delete(0, tk.END)  # Очищаем поле ввода для повторного ввода
                

        # Кнопка подтверждения пароля
        submit_button = tk.Button(window, text="ОК", command=on_submit, width=20)  # Ширина кнопки
        submit_button.pack(pady=(5, 10))  # Кнопка теперь расположена ближе к полю ввода

        # Привязываем клавишу Enter к кнопке для активации нажатия
        window.bind('<Return>', lambda event: on_submit())

     
        # Запуск окна
        window.mainloop()


def is_program_already_running():
    """
    Проверяет, запущена ли программа через системный мьютекс.
    Если программа уже запущена, возвращает True.
    """
    mutex_name = "Global\\AntitheftProgramMutex"  # Уникальное имя мьютекса
    # Создаём мьютекс
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    
    # Проверяем, существует ли уже мьютекс
    if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        return True
    return False

def main():
    
    if is_program_already_running():
        print("[ОШИБКА] Программа уже запущена. Повторный запуск невозможен.")
        sys.exit(1)

    # Отключение кнопки питания   
    set_lid_close_action()
    # Проверка существования пароля в реестре
    stored_password = read_password_from_registry()
    if stored_password is None:
        show_console()
        disable_device()
        set_system_time()
        print("[УСТАНОВКА] Проверьте язык клавиатуры и установите новый пароль.")
        password = input("Введите новый пароль: ").strip()
        if password:
            save_password(password)
            print("[ИНФО] Пароль сохранён в реестре.")
            disable_shutdown_buttons_and_control_panel()
        else:
            print("[ОШИБКА] Пароль не установлен. Программа завершена.")
            return        
    else:
        print("[ИНФО] Найден сохранённый пароль.")   

    print("[ИНФО] Антикражная защита активирована. Программа работает!")
    hide_console()
    
    threading.Thread(target=check_time_and_shutdown, daemon=True).start()
    threading.Thread(target=monitor_power, daemon=True).start()
    threading.Thread(target=monitor_volume, daemon=True).start()    
    threading.Thread(target=create_notification_window, daemon=True).start()
   
  
    while True:
        prevent_sleep_mode()
        time.sleep(3)
       

if __name__ == "__main__":   
    main()
   
    
