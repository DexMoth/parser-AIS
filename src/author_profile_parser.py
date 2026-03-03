
from bs4 import BeautifulSoup
import re
import logging

class AuthorProfileParser:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse(self, html, author_id=None):
        if not html:
            self.logger.error("HTML-код не предоставлен")
            return None
        
        soup = BeautifulSoup(html, 'lxml')
        author_data = {
            'author_id': author_id,
            'full_name': None,
            'organization': None,
            'spin_code': None,
            'positions': [], # веб просит, существует, даже если нет мест работы
            'publications_total': 0,
            'publications_risc': 0,
            'citations_total': 0,
            'citations_risc': 0,
            'h_index_risc': 0,
            'h_index_without_self': 0,
            'coauthors_count': 0,
            'first_publication_year': None
        }
        
        # сохраняем html для отладки
        with open(f'debug_profile_{author_id}.html', 'w', encoding='utf-8') as f:
            f.write(html)
        self.logger.info(f"html сохранен в debug_profile_{author_id}.html")

        # основная инфа
        self._parse_main_info(soup, author_data)
        
        # места работы
        self._parse_positions(soup, author_data)
        
        # показатели
        self._parse_metrics(soup, author_data)
        
        return author_data
    
    def _parse_main_info(self, soup, author_data):
        name_div = soup.find('div', style=re.compile(r'width:540px'))
        if name_div:
            name_tag = name_div.find('font', color='#F26C4F')
            if name_tag:
                name_bold = name_tag.find('b')
                if name_bold:
                    author_data['full_name'] = name_bold.get_text(strip=True)
                    self.logger.info(f"найдено имя: {author_data['full_name']}")
        
        if name_div:
            org_link = name_div.find('a', href=re.compile(r'org_profile\.asp\?id='))
            if org_link:
                author_data['organization'] = org_link.get_text(strip=True)
                self.logger.info(f"найдена организация: {author_data['organization']}")
            
            # SPIN-код и AuthorID
            text = name_div.get_text()
            spin_match = re.search(r'SPIN-код:\s*(\d+-\d+)', text)
            if spin_match:
                author_data['spin_code'] = spin_match.group(1)
                self.logger.info(f"найден spin: {author_data['spin_code']}")
            
            authorid_match = re.search(r'AuthorID:\s*(\d+)', text)
            if authorid_match:
                author_data['author_id'] = authorid_match.group(1)
    
    def _parse_positions(self, soup, author_data):
        positions_section = soup.find('div', class_='midtext', string=re.compile('МЕСТО РАБОТЫ'))
        if positions_section:
            table = positions_section.find_next('table', width='520')
            if table:
                rows = table.find_all('tr')
                for row in rows[2:]:  # пропускаем заголовок и разделитель
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        org_cell = cells[1]
                        period_cell = cells[2]
                        count_cell = cells[3]
                        
                        org_link = org_cell.find('a')
                        org_name = org_link.get_text(strip=True) if org_link else org_cell.get_text(strip=True)
                        
                        position = {
                            'organization': org_name,
                            'period': period_cell.get_text(strip=True),
                            'publications': count_cell.get_text(strip=True)
                        }
                        author_data['positions'].append(position)
    
    def _parse_metrics(self, soup, author_data):
        metrics_section = soup.find('div', class_='midtext', string=re.compile('ОБЩИЕ ПОКАЗАТЕЛИ'))
        if metrics_section:
            table = metrics_section.find_next('table', width='580')
            if table:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        # пропускаем строки с иконками помощи
                        if cells[0].find('img', class_='imghelp'):
                            metric_name = cells[1].get_text(strip=True)
                            metric_value = cells[2].get_text(strip=True)
                            
                            # определяем тип метрики по названию
                            self._map_metric(metric_name, metric_value, author_data)
    
    def _map_metric(self, name, value, author_data):
        name_lower = name.lower()
        
        if 'число публикаций на elibrary.ru' in name_lower:
            author_data['publications_total'] = self._extract_number(value)
        elif 'число публикаций в ринц' in name_lower:
            author_data['publications_risc'] = self._extract_number(value)
        elif 'число публикаций, входящих в ядро ринц' in name_lower:
            author_data['publications_core'] = self._extract_number(value)
        
        elif 'число цитирований из публикаций на elibrary.ru' in name_lower:
            author_data['citations_total'] = self._extract_number(value)
        elif 'число цитирований из публикаций, входящих в ринц' in name_lower:
            author_data['citations_risc'] = self._extract_number(value)
        elif 'число цитирований из публикаций, входящих в ядро ринц' in name_lower:
            author_data['citations_core'] = self._extract_number(value)
        
        elif 'индекс хирша по всем публикациям на elibrary.ru' in name_lower:
            author_data['h_index_total'] = self._extract_number(value)
        elif 'индекс хирша по публикациям в ринц' in name_lower:
            author_data['h_index_risc'] = self._extract_number(value)
        elif 'индекс хирша по ядру ринц' in name_lower:
            author_data['h_index_core'] = self._extract_number(value)
        elif 'индекс хирша без учета самоцитирований' in name_lower:
            author_data['h_index_without_self'] = self._extract_number(value)
        
        elif 'число публикаций, процитировавших работы автора' in name_lower:
            author_data['citing_publications'] = self._extract_number(value)
        elif 'число ссылок на самую цитируемую публикацию' in name_lower:
            author_data['max_citations'] = self._extract_number(value)
        elif 'число публикаций автора, процитированных хотя бы один раз' in name_lower:
            match = re.search(r'(\d+)', value)
            if match:
                author_data['cited_publications'] = int(match.group(1))
        elif 'среднее число цитирований в расчете на одну публикацию' in name_lower:
            match = re.search(r'([\d,]+)', value)
            if match:
                author_data['avg_citations'] = float(match.group(1).replace(',', '.'))
        elif 'число самоцитирований' in name_lower:
            match = re.search(r'(\d+)', value)
            if match:
                author_data['self_citations'] = int(match.group(1))
        elif 'число соавторов' in name_lower:
            author_data['coauthors_count'] = self._extract_number(value)
        elif 'число статей в российских журналах из перечня вак' in name_lower:
            match = re.search(r'(\d+)', value)
            if match:
                author_data['vak_articles'] = int(match.group(1))
        elif 'год первой публикации' in name_lower:
            match = re.search(r'\d{4}', value)
            if match:
                author_data['first_publication_year'] = int(match.group(0))
    
    # число из текста
    def _extract_number(self, text):
        match = re.search(r'\d+', text)
        return int(match.group()) if match else 0