import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

class Requester:
    """класс для работы с elibrary через selenium"""
    
    def __init__(self, delay_min=40, delay_max=60, timeout=30):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.is_authenticated = False
    
    def _setup_driver(self):
        """настройка браузера"""

        options = Options()
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        
        # можно скрыть окно браузера, раскомментировав следующую строку
        # options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1024, 768)
    
    def login(self, login, password):
        """авторизация через selenium"""
        self.logger.info("вход в систему через браузер...")
        
        try:
            if not self.driver:
                self._setup_driver()
            
            # открываем главную страницу
            self.driver.get("https://www.elibrary.ru/defaultx.asp?session=off")
            time.sleep(3)
            
            # ищем форму входа
            login_container = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'win_login'))
            )
            
            # заполняем логин и пароль
            login_field = login_container.find_element(By.ID, 'login')
            password_field = login_container.find_element(By.ID, 'password')
            
            login_field.clear()
            login_field.send_keys(login)
            password_field.clear()
            password_field.send_keys(password)
            
            # чекбокс "запомнить меня" (снимаем)
            try:
                checkbox = login_container.find_element(By.NAME, 'knowme')
                if checkbox.is_selected():
                    checkbox.click()
            except:
                pass
            
            # нажимаем кнопку входа
            login_button = login_container.find_element(By.CLASS_NAME, 'butred')
            login_button.click()
            
            # ждем результат
            time.sleep(5)
            
            # проверяем успешность
            if 'Имя пользователя' in self.driver.page_source and 'Незарегистрированный' not in self.driver.page_source:
                self.is_authenticated = True
                self.logger.info("успешный вход!")
                return True
            else:
                self.logger.error("не удалось войти")
                return False
                
        except Exception as e:
            self.logger.error(f"ошибка при входе: {e}")
            return False
    
    def get_page(self, url, params=None, referer=None):
        """получить html страницы через selenium"""
        if not self.driver:
            self.logger.error("браузер не инициализирован")
            return None
        
        try:
            # добавляем параметры к url если есть
            if params:
                from urllib.parse import urlencode
                separator = '&' if '?' in url else '?'
                url = f"{url}{separator}{urlencode(params)}"
            
            self.logger.info(f"загрузка: {url}")
            self.driver.get(url)
            time.sleep(3)  # ждем загрузку
            return self.driver.page_source
            
        except Exception as e:
            self.logger.error(f"ошибка загрузки {url}: {e}")
            return None
    
    def logout(self):
        """выход из системы"""
        if not self.driver:
            return True
        
        try:
            self.logger.info("выход из системы...")
            # можно перейти на страницу выхода
            self.driver.get("https://www.elibrary.ru/end_session.asp")
            time.sleep(2)
            self.driver.quit()
            self.driver = None
            self.is_authenticated = False
            self.logger.info("выход выполнен")
            return True
        except Exception as e:
            self.logger.error(f"ошибка при выходе: {e}")
            return False