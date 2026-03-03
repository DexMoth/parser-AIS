import logging
from requester import Requester
from author_profile_parser import AuthorProfileParser
from author_refs_parser import AuthorRefsParser
from author_items_parser import AuthorItemsParser
from config import USE_LOGIN_FROM_CONFIG, LOGIN_DATA, DELAY_MIN, DELAY_MAX, TIMEOUT, BASE_URL
import csv
from pathlib import Path

class ElibraryParser:
    """
    парсинг всех страниц eLibrary.ru
    """
    
    def __init__(self, delay=3):
        self.requester = Requester(
            delay_min=DELAY_MIN,
            delay_max=DELAY_MAX,
            timeout=TIMEOUT
        )
        self.profile_parser = AuthorProfileParser()
        self.refs_parser = AuthorRefsParser()
        self.items_parser = AuthorItemsParser()
        self.logger = logging.getLogger(__name__)
        self.authenticated = False
        self.base_url = BASE_URL

    def authenticate(self, login=None, password=None, show_browser=False):
        if USE_LOGIN_FROM_CONFIG:
            # берем данные из конфига
            login = LOGIN_DATA.get('login')
            password = LOGIN_DATA.get('password')
            self.logger.info("данные из config.json")
        else:
            # запрашиваем ввод
            if not login or not password:
                login = input("введите логин: ")
                password = input("введите пароль: ")
        
        if not login or not password:
            self.logger.error("логин и пароль не указаны")
            return False
        
        self.authenticated = self.requester.login(login, password)
        return self.authenticated
    
    def logout(self):
        return self.requester.logout()

    def get_author_profile(self, author_id):
        """
        Получение данных профиля автора
        """
        if not self.authenticated:
            self.logger.error("нет авторизации")
            return None
        
        url = f"{self.base_url}/author_profile.asp"
        params = {'authorid': author_id}
        
        html = self.requester.get_page(url, params=params, referer=self.base_url)
        if html:
            return self.profile_parser.parse(html, author_id=author_id)
        else:
            self.logger.error(f"Не удалось загрузить профиль автора с ID {author_id}")
            return None
    
    def get_author_refs(self, author_id, page=1):
        """
        Получение списка цитирований автора
        """
        if not self.authenticated:
                self.logger.error("нет авторизации")
                return None
        
        max_pages=20
        all_refs = []
        current_page = 1
        total_refs = 0
        
        self.logger.info(f"Начинаем сбор всех цитирований автора {author_id}")
    
        while current_page <= max_pages:
            # формируем URL с номером страницы
            url = f"{self.base_url}/author_refs.asp?authorid={author_id}&pagenum={current_page}"
            
            self.logger.info(f"Загрузка страницы {current_page}: {url}")
            
            html = self.requester.get_page(url, referer=f"{self.base_url}/author_profile.asp?authorid={author_id}")
            
            if not html:
                self.logger.error(f"Не удалось загрузить страницу {current_page}")
                break
            
            result = self.refs_parser.parse(html, author_id=author_id)
            
            if not result:
                self.logger.error(f"Ошибка парсинга страницы {current_page}")
                break
            
            refs = result.get('refs', [])
            if not refs:
                self.logger.info(f"На странице {current_page} нет цитирований, завершаем")
                break
            
            all_refs.extend(refs)
            self.logger.info(f"Страница {current_page}: +{len(refs)} цитирований")
            
            # получаем общее количество с первой страницы
            if current_page == 1:
                total_refs = result.get('total_refs', 0)
                self.logger.info(f"Всего цитирований по данным сайта: {total_refs}")
            
            # проверяем, есть ли следующая страница по количеству полученных цитирований
            if len(refs) < 100:
                self.logger.info(f"На странице меньше 100 цитирований, это последняя страница")
                break
            
            current_page += 1
            import time
            time.sleep(2)  # задержка между страницами
        
        self.logger.info(f"Всего собрано цитирований: {len(all_refs)}")
        
        return {
            'author_id': author_id,
            'total_refs': total_refs or len(all_refs),
            'refs': all_refs
        }
    
    def get_author_items(self, author_id, page=1):
        """
        Получение списка публикаций автора (все страницы)
        """
        if not self.authenticated:
            self.logger.error("нет авторизации")
            return None
        
        all_publications = []
        current_page = 1
        max_pages = 50  # максимальное количество страниц
        total_publications = 0
        
        self.logger.info(f"Начинаем сбор всех публикаций автора {author_id}")
        
        while current_page <= max_pages:
            # формируем URL с номером страницы
            url = f"{self.base_url}/author_items.asp?authorid={author_id}&pagenum={current_page}"
            
            self.logger.info(f"Загрузка страницы {current_page}: {url}")
            
            html = self.requester.get_page(url, referer=f"{self.base_url}/author_profile.asp?authorid={author_id}")
            
            if not html:
                self.logger.error(f"Не удалось загрузить страницу {current_page}")
                break
            
            result = self.items_parser.parse(html, author_id=author_id)
            
            if not result:
                self.logger.error(f"Ошибка парсинга страницы {current_page}")
                break
            
            publications = result.get('publications', [])
            if not publications:
                self.logger.info(f"На странице {current_page} нет публикаций, завершаем")
                break
            
            all_publications.extend(publications)
            self.logger.info(f"Страница {current_page}: +{len(publications)} публикаций")
            
            # получаем общее количество с первой страницы
            if current_page == 1:
                total_publications = result.get('total_publications', 0)
                self.logger.info(f"Всего публикаций по данным сайта: {total_publications}")
            
            # проверяем, есть ли следующая страница по количеству полученных публикаций
            if len(publications) < 100:
                self.logger.info(f"На странице меньше 100 публикаций, это последняя страница")
                break
            
            current_page += 1
            import time
            time.sleep(2)  # задержка между страницами
        
        self.logger.info(f"Всего собрано публикаций: {len(all_publications)}")
        
        return {
            'author_id': author_id,
            'total_publications': total_publications or len(all_publications),
            'publications': all_publications
        }
    
    def get_all_author_data(self, author_id, max_pages=10):
        """
        Получение всех данных об авторе (профиль + все страницы публикаций и цитирований)
        """
        result = {
            'profile': None,
            'publications': [],
            'refs': []
        }
        
        # профиль
        self.logger.info(f"Загрузка профиля автора {author_id}")
        result['profile'] = self.get_author_profile(author_id)
        
        if not result['profile']:
            self.logger.error(f"Не удалось получить профиль автора {author_id}")
            return result
        
        # публикации (страница 1)
        self.logger.info(f"Загрузка публикаций автора {author_id}, страница 1")
        pubs_page1 = self.get_author_items(author_id, page=1)
        
        if pubs_page1:
            result['publications'].extend(pubs_page1.get('publications', []))
            
            # Если есть следующие страницы
            total_pubs = pubs_page1.get('total_publications', 0)
            per_page = pubs_page1.get('page_to', 100) - pubs_page1.get('page_from', 1) + 1
            
            if per_page > 0:
                total_pages = (total_pubs + per_page - 1) // per_page
                
                for page in range(2, min(total_pages, max_pages) + 1):
                    self.logger.info(f"Загрузка публикаций автора {author_id}, страница {page}")
                    pubs_page = self.get_author_items(author_id, page=page)
                    if pubs_page:
                        result['publications'].extend(pubs_page.get('publications', []))
        
        # цитирования (страница 1)
        self.logger.info(f"Загрузка цитирований автора {author_id}, страница 1")
        refs_page1 = self.get_author_refs(author_id, page=1)
        
        if refs_page1:
            result['refs'].extend(refs_page1.get('refs', []))
            
            # Если есть следующие страницы
            total_refs = refs_page1.get('total_refs', 0)
            per_page = refs_page1.get('page_to', 100) - refs_page1.get('page_from', 1) + 1
            
            if per_page > 0:
                total_pages = (total_refs + per_page - 1) // per_page
                
                for page in range(2, min(total_pages, max_pages) + 1):
                    self.logger.info(f"Загрузка цитирований автора {author_id}, страница {page}")
                    refs_page = self.get_author_refs(author_id, page=page)
                    if refs_page:
                        result['refs'].extend(refs_page.get('refs', []))
        
        return result
    
    def save_publications_to_csv(self, publications, filename):
        """Сохранение публикаций в CSV"""
        if not publications:
            return
        
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        filepath = output_dir / filename
        
        fieldnames = ['number', 'title', 'authors', 'source_info', 'year', 
                     'citations', 'publication_id', 'url', 'is_from_refs']
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for pub in publications:
                #  только нужные поля
                row = {k: pub.get(k, '') for k in fieldnames}
                writer.writerow(row)
        
        self.logger.info(f"Публикации сохранены в {filepath}")
        return str(filepath)
    
    def save_refs_to_csv(self, refs, filename):
        """Сохранение цитирований в CSV"""
        if not refs:
            return
        
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        
        filepath = output_dir / filename
        
        fieldnames = ['number', 'cited_work', 'source_title', 'source_authors', 
                     'source_year', 'context', 'edn', 'cited_url', 'source_url']
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for ref in refs:
                # только нужные поля
                row = {k: ref.get(k, '') for k in fieldnames}
                writer.writerow(row)
        
        self.logger.info(f"Цитирования сохранены в {filepath}")
        return str(filepath)