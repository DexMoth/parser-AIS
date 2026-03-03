from bs4 import BeautifulSoup
import re
import logging

class AuthorRefsParser:  
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse(self, html, author_id=None):
        if not html:
            self.logger.error("HTML-код не предоставлен")
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        result = {
            'author_id': author_id,
            'author_name': None,
            'total_refs': 0,
            'page_from': 0,
            'page_to': 0,
            'refs': []
        }
        
        # инфа об авторе
        self._parse_author_info(soup, result)
        
        # инфа о цитированиях
        self._parse_total_info(soup, result)
        
        # список цитирований
        self._parse_refs_list(soup, result)
        
        return result
    
    def _parse_author_info(self, soup, result):
        name_div = soup.find('div', style=re.compile(r'width:540px'))
        if name_div:
            name_tag = name_div.find('font', color='#F26C4F')
            if name_tag:
                name_bold = name_tag.find('b')
                if name_bold:
                    result['author_name'] = name_bold.get_text(strip=True)
    
    def _parse_total_info(self, soup, result):
        info_div = soup.find('div', class_='redref')
        if info_div:
            text = info_div.get_text()
            
            # Поиск общего количества
            total_match = re.search(r'Всего найдена\s+(\d+)\s+ссылка', text)
            if total_match:
                result['total_refs'] = int(total_match.group(1))
            
            # Поиск диапазона на странице
            range_match = re.search(r'с\s+(\d+)\s+по\s+(\d+)', text)
            if range_match:
                result['page_from'] = int(range_match.group(1))
                result['page_to'] = int(range_match.group(2))
    
    def _parse_refs_list(self, soup, result):
        ref_rows = soup.find_all('tr', id=re.compile(r'^arw\d+'))
        
        for row in ref_rows:
            ref_data = self._parse_ref_row(row)
            if ref_data:
                result['refs'].append(ref_data)
        
        self.logger.info(f"Найдено {len(result['refs'])} цитирований на странице")
    
    def _parse_ref_row(self, row):
        ref_data = {}
        
        # Извлечение номера
        number_cell = row.find('td', class_='select-tr-left')
        if number_cell:
            number_b = number_cell.find('b')
            if number_b:
                ref_data['number'] = number_b.get_text(strip=True).replace('.', '')
        
        # Извлечение цитируемой работы
        content_cell = row.find('td', class_='select-tr-right')
        if not content_cell:
            return None
        
        cited_block = content_cell.find('font', color='#00008f')
        if cited_block:
            ref_data['cited_work'] = cited_block.get_text(strip=True)
            
            # Поиск EDN
            edn_link = content_cell.find('a', href=re.compile(r'elibrary\.ru/\w+'))
            if edn_link and 'EDN:' in content_cell.get_text():
                ref_data['edn'] = edn_link.get_text(strip=True)
        
        # Источник
        source_tables = content_cell.find_all('table', width='100%')
        for table in source_tables:
            cells = table.find_all('td')
            if len(cells) >= 2 and 'Источник:' in cells[0].get_text():
                source_cell = cells[1]
                source_link = source_cell.find('a')
                if source_link:
                    ref_data['source_title'] = source_link.get_text(strip=True)
                    
                    # авторы источника
                    author_i = source_cell.find('i')
                    if author_i:
                        ref_data['source_authors'] = author_i.get_text(strip=True)
                    
                    # год и детали
                    source_text = source_cell.get_text()
                    year_match = re.search(r'20\d{2}', source_text)
                    if year_match:
                        ref_data['source_year'] = int(year_match.group(0))
                    
                    # URL источника
                    if source_link.get('href'):
                        ref_data['source_url'] = 'https://elibrary.ru/' + source_link['href']
                
                # ссылка
                go_link = content_cell.find('a', href=re.compile(r'item\.asp\?id='))
                if go_link and go_link.get('href'):
                    ref_data['cited_url'] = 'https://elibrary.ru/' + go_link['href']
        
        for table in source_tables:
            cells = table.find_all('td')
            if len(cells) >= 2 and 'Контекст:' in cells[0].get_text():
                context_cell = cells[1]
                context_text = context_cell.get_text(strip=True)
                if context_text:
                    ref_data['context'] = context_text
        
        return ref_data