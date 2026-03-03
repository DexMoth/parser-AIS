from bs4 import BeautifulSoup
import re
import logging

class AuthorItemsParser:
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
            'total_publications': 0,
            'total_citations': 0,
            'page_from': 0,
            'page_to': 0,
            'publications': []
        }
    

        # инфа об авторе
        self._parse_author_info(soup, result)
        
        # общая инфа
        self._parse_total_info(soup, result)
        
        # список публикаций
        self._parse_publications_list(soup, result)
        
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
            
            # число публикаций
            pubs_match = re.search(r'Всего найдено\s+(\d+)\s+публикаций', text)
            if pubs_match:
                result['total_publications'] = int(pubs_match.group(1))
            
            # число цитирований
            cites_match = re.search(r'количеством цитирований:\s*(\d+)', text)
            if cites_match:
                result['total_citations'] = int(cites_match.group(1))
            
            # поиск диапазона на странице
            range_match = re.search(r'с\s+(\d+)\s+по\s+(\d+)', text)
            if range_match:
                result['page_from'] = int(range_match.group(1))
                result['page_to'] = int(range_match.group(2))
    
    def _parse_publications_list(self, soup, result):
        pub_rows = soup.find_all('tr', id=re.compile(r'^(arw|brw)\d+'))
        
        self.logger.info(f"найдено строк с публикациями: {len(pub_rows)}")
        
        for row in pub_rows:
            pub_data = self._parse_publication_row(row)
            if pub_data:
                result['publications'].append(pub_data)
        
        self.logger.info(f"распаршено публикаций: {len(result['publications'])}")
    
    def _parse_publication_row(self, row):
        pub_data = {
            'is_from_refs': 'brw' in row.get('id', ''),
            'number': None,
            'title': None,
            'authors': None,
            'source_info': None,
            'year': None,
            'citations': 0,
            'publication_id': None,
            'url': None
        }
        
        # номер публикации (из левой ячейки)
        number_cell = row.find('td', class_='select-tr-left')
        if number_cell:
            number_b = number_cell.find('b')
            if number_b:
                pub_data['number'] = number_b.get_text(strip=True).replace('.', '')
        
        # правая ячейка
        content_cell = row.find('td', class_='select-tr-right')
        if not content_cell:
            return None
        
        # середина
        cell = row.find('td', attrs={'align': 'left'})
        
         # НАЗВАНИЕ - ищем ссылку на /item.asp
        title_link = cell.find('a', href=lambda x: x and 'item.asp' in x)
        if title_link:
            # self.logger.info(f"найдена ссылка: {title_link}")
            # название внутри <b><span>...</span></b>
            title_span = title_link.find('span')
            if title_span:
                pub_data['title'] = title_span.get_text(strip=True)
                # self.logger.info(f"название из span: {pub_data['title']}")
            
            href = title_link.get('href', '')
            if href:
                pub_data['url'] = 'https://www.elibrary.ru' + href
                id_match = re.search(r'id=(\d+)', href)
                if id_match:
                    pub_data['publication_id'] = id_match.group(1)
        
        # АВТОРЫ - ищем <i> внутри <font color="#00008f">
        author_font = cell.find('font', color='#00008f')
        if author_font:
            author_i = author_font.find('i')
            if author_i:
                pub_data['authors'] = author_i.get_text(strip=True)
        
        # ИСТОЧНИК ИНФОРМАЦИИ - берем весь текст после авторов
        all_text = cell.get_text()
        
        journal_link = cell.find('a', href=re.compile(r'/contents\.asp\?id='))

        if journal_link and pub_data['authors']:
            # это статья - есть ссылка на журнал
            parts = all_text.split(pub_data['authors'])
            if len(parts) > 1:
                pub_data['source_info'] = parts[1].strip()
        else:
            # учебное пособие или другой тип - источник не заполняем
            pub_data['source_info'] = "—"

        # год ищем всегда
        desc = cell.find('font', color='#00008f')
        if desc:
            text = desc.get_text()
            year_match = re.search(r'\b(19|20)\d{2}\b', text)
            if year_match:
                pub_data['year'] = int(year_match.group(0))
            else:
               # если в первом нет, ищем второй font
                all_fonts = cell.find_all('font', color='#00008f')
                if len(all_fonts) > 1:
                    second_font = all_fonts[1]
                    second_text = second_font.get_text()
                    year_match = re.search(r'\b(19|20)\d{2}\b', second_text)
                    if year_match:
                        pub_data['year'] = int(year_match.group(0))
        if not pub_data.get('year'):
            pub_data['year'] = None

        # ЦИТИРОВАНИЯ (последняя ячейка с числом)
        # ищем все ячейки с классом select-tr-right
        cite_cell = row.find('td', class_='select-tr-right')
        if cite_cell:
            cite_text = cite_cell.get_text(strip=True)
            # пытаемся преобразовать в число, если это возможно
            try:
                pub_data['citations'] = int(cite_text) if cite_text.isdigit() else 0
            except:
                pub_data['citations'] = 0
        
        return pub_data