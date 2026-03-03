import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from datetime import datetime
import os
import sys
import csv
import json
from collections import Counter
import logging

LOGIN = "Исаева Александра"
PASSWORD = "9/4209/3"
# чтобы не заблокали
DELAY = 15

# Добавляем путь к src в sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from elibrary_parser import ElibraryParser

class MainWindow:
    """Главное окно приложения Парсер eLibrary.ru"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Парсер eLibrary.ru")
        self.root.geometry("1000x700")
        
        # Определяем пути
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.root_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Инициализация парсера и логгера
        self.parser = ElibraryParser(delay=DELAY)
        self._setup_logging()
        self.logger = logging.getLogger(__name__)

        login = LOGIN
        password = PASSWORD

        if self.parser.authenticate(login, password):
            print("авторизация успешна")
        else:
            print("ошибка авторизации")
            messagebox.showerror("Ошибка", "Не удалось авторизоваться")

        # Текущие данные
        self.current_author_id = None
        self.current_profile = None
        self.current_publications = []
        self.current_refs = []
        
        # Создание интерфейса
        self._create_widgets()
        
    def _create_widgets(self):
        """Создание элементов интерфейса"""
        
        # ======= Верхняя панель с поиском =======
        top_frame = ttk.Frame(self.root, padding="5")
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="ID автора:").pack(side=tk.LEFT, padx=5)
        self.id_entry = ttk.Entry(top_frame, width=20)
        self.id_entry.pack(side=tk.LEFT, padx=5)
        self.id_entry.bind('<Return>', lambda e: self.search_author())
        
        self._create_entry_context_menu()

        self.search_btn = ttk.Button(top_frame, text="Поиск", command=self.search_author)
        self.search_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(top_frame, text="Сохранить в CSV", command=self.save_to_csv)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # повторная авторизация
        self.reauth_btn = ttk.Button(top_frame, text="Повторный вход", 
                                    command=self.reauthenticate)
        self.reauth_btn.pack(side=tk.LEFT, padx=5)

        # Статус
        self.status_label = ttk.Label(top_frame, text="Готов")
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # ======= Панель с вкладками =======
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Вкладка 1: Профиль автора
        self._create_profile_tab()
        
        # Вкладка 2: Публикации
        self._create_publications_tab()
        
        # Вкладка 3: Цитирования
        self._create_refs_tab()
        
        # Вкладка 4: Статистика
        self._create_stats_tab()
    
    def _setup_logging(self):
        """настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()  # вывод в консоль
            ]
        )

    def _create_profile_tab(self):
        """Вкладка профиля автора"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Профиль автора")
        
        # ФИО
        fio_frame = ttk.Frame(frame, padding="10")
        fio_frame.pack(fill=tk.X)
        ttk.Label(fio_frame, text="ФИО:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.fio_label = ttk.Label(fio_frame, text="—", font=('Arial', 10))
        self.fio_label.pack(side=tk.LEFT, padx=10)
        
        # Организация
        org_frame = ttk.Frame(frame, padding="10")
        org_frame.pack(fill=tk.X)
        ttk.Label(org_frame, text="Организация:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.org_label = ttk.Label(org_frame, text="—", font=('Arial', 10))
        self.org_label.pack(side=tk.LEFT, padx=10)
        
        # SPIN и AuthorID
        id_frame = ttk.Frame(frame, padding="10")
        id_frame.pack(fill=tk.X)
        ttk.Label(id_frame, text="SPIN:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.spin_label = ttk.Label(id_frame, text="—", font=('Arial', 10))
        self.spin_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(id_frame, text="AuthorID:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(20,0))
        self.authorid_label = ttk.Label(id_frame, text="—", font=('Arial', 10))
        self.authorid_label.pack(side=tk.LEFT, padx=10)
        
        # Метрики
        metrics_frame = ttk.LabelFrame(frame, text="Наукометрические показатели", padding="10")
        metrics_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Создаем таблицу метрик
        metrics = [
            ("Публикаций на elibrary.ru:", "pubs_total"),
            ("Публикаций в РИНЦ за последние 5 лет:", "pubs_risc"),
            ("Цитирований на elibrary.ru:", "cites_total"),
            ("Цитирований в РИНЦ:", "cites_risc"),
            ("Индекс Хирша:", "h_index"),
            ("Хирш без самоцит.:", "h_index_self"),
            ("Соавторов:", "coauthors"),
            ("Год первой публ.:", "first_year")
        ]
        
        for i, (label, attr) in enumerate(metrics):
            ttk.Label(metrics_frame, text=label, width=39, anchor=tk.W).grid(row=i//2, column=(i%2)*2, sticky=tk.W, pady=2)
            setattr(self, attr + "_label", ttk.Label(metrics_frame, text="0", font=('Arial', 10, 'bold')))
            getattr(self, attr + "_label").grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=10, pady=2)

        # добавляем простое текстовое поле для организации (если нужно)
        org_detail_frame = ttk.LabelFrame(frame, text="Место работы", padding="10")
        org_detail_frame.pack(fill=tk.X, padx=10, pady=5)
        self.org_detail_label = ttk.Label(org_detail_frame, text="", wraplength=800)
        self.org_detail_label.pack(anchor=tk.W)
    
    def _create_publications_tab(self):
        """Вкладка со списком публикаций"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Публикации")
        
        # Информация о количестве
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        self.pubs_info = ttk.Label(info_frame, text="Публикации не загружены")
        self.pubs_info.pack(side=tk.LEFT)
        
        ttk.Button(info_frame, text="↕️ Сортировать по цитированиям", 
            command=self.sort_publications_by_citations).pack(side=tk.RIGHT, padx=5)

        # Таблица публикаций
        columns = ('#', 'Название', 'Журнал', 'Год', 'Цит.')
        self.pubs_tree = ttk.Treeview(frame, columns=columns, show='headings', height=20)
        
        self.pubs_tree.heading('#', text='#', command=lambda: self.sort_publications('#'))
        self.pubs_tree.heading('Название', text='Название', command=lambda: self.sort_publications('Название'))
        self.pubs_tree.heading('Журнал', text='Журнал/Источник', command=lambda: self.sort_publications('Журнал'))
        self.pubs_tree.heading('Год', text='Год', command=lambda: self.sort_publications('Год'))
        self.pubs_tree.heading('Цит.', text='Цит.', command=lambda: self.sort_publications('Цит.'))
        
        self.pubs_tree.column('#', width=40, anchor='center')
        self.pubs_tree.column('Название', width=300)
        self.pubs_tree.column('Журнал', width=250)
        self.pubs_tree.column('Год', width=60, anchor='center')
        self.pubs_tree.column('Цит.', width=60, anchor='center')
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.pubs_tree.yview)
        self.pubs_tree.configure(yscrollcommand=scrollbar.set)
        
        self.pubs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.sort_reverse = False
        self.last_sort_column = 'Цит.'
    
    def _create_refs_tab(self):
        """Вкладка со списком цитирований"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Цитирования")
        
        # Информация о количестве
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        self.refs_info = ttk.Label(info_frame, text="Цитирования не загружены")
        self.refs_info.pack(side=tk.LEFT)
        
        # Таблица цитирований
        columns = ('#', 'Цитируемая работа', 'Источник', 'Год')
        self.refs_tree = ttk.Treeview(frame, columns=columns, show='headings', height=20)
        
        self.refs_tree.heading('#', text='#')
        self.refs_tree.heading('Цитируемая работа', text='Цитируемая работа')
        self.refs_tree.heading('Источник', text='Источник')
        self.refs_tree.heading('Год', text='Год')
        
        self.refs_tree.column('#', width=40, anchor='center')
        self.refs_tree.column('Цитируемая работа', width=350)
        self.refs_tree.column('Источник', width=350)
        self.refs_tree.column('Год', width=60, anchor='center')
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.refs_tree.yview)
        self.refs_tree.configure(yscrollcommand=scrollbar.set)
        
        self.refs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_stats_tab(self):
        """Вкладка со статистикой"""
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text="Статистика")
        
        # Основные показатели
        main_frame = ttk.LabelFrame(frame, text="Основные показатели", padding="10")
        main_frame.pack(fill=tk.X, pady=5)
        
        stats_grid = ttk.Frame(main_frame)
        stats_grid.pack()
        
        ttk.Label(stats_grid, text="Всего публикаций:", width=20, anchor=tk.W).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.stat_total_pubs = ttk.Label(stats_grid, text="0", font=('Arial', 10, 'bold'))
        self.stat_total_pubs.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(stats_grid, text="Всего цитирований:", width=20, anchor=tk.W).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.stat_total_cites = ttk.Label(stats_grid, text="0", font=('Arial', 10, 'bold'))
        self.stat_total_cites.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(stats_grid, text="Среднее цитирование:", width=20, anchor=tk.W).grid(row=2, column=0, sticky=tk.W, pady=2)
        self.stat_avg_cites = ttk.Label(stats_grid, text="0", font=('Arial', 10, 'bold'))
        self.stat_avg_cites.grid(row=2, column=1, sticky=tk.W, padx=10)
        
        # Самая цитируемая статья
        top_frame = ttk.LabelFrame(frame, text="Самая цитируемая публикация", padding="10")
        top_frame.pack(fill=tk.X, pady=10)
        
        self.top_title = ttk.Label(top_frame, text="—", wraplength=800)
        self.top_title.pack(anchor=tk.W)
        self.top_info = ttk.Label(top_frame, text="")
        self.top_info.pack(anchor=tk.W, pady=5)
        
        # Распределение по годам
        years_frame = ttk.LabelFrame(frame, text="Распределение по годам", padding="10")
        years_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.years_text = tk.Text(years_frame, height=8, wrap=tk.NONE)
        self.years_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(years_frame, orient=tk.VERTICAL, command=self.years_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.years_text.configure(yscrollcommand=scrollbar.set)
        self.years_text.config(state=tk.DISABLED)
    
    def search_author(self):
        """Поиск автора по ID"""
        author_id = self.id_entry.get().strip()
        if not author_id:
            messagebox.showwarning("Предупреждение", "Введите ID автора")
            return
        
        self.current_author_id = author_id
        self.status_label.config(text="Загрузка...")
        self.search_btn.config(state=tk.DISABLED)
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=self._load_author_thread, args=(author_id,))
        thread.daemon = True
        thread.start()
    
    def _load_author_thread(self, author_id):
        """Загрузка данных в отдельном потоке"""
        self.logger.info("загрузка автора...")
        try:
            # Загружаем профиль
            profile = self.parser.get_author_profile(author_id)
            
            if profile:
                self.current_profile = profile
                self.root.after(0, self._update_profile_display, profile)
                
                self.logger.info("загрузка публикаций...")
                pubs = self.parser.get_author_items(author_id)
                if pubs:
                    pubs_list = pubs.get('publications', [])
                    self.logger.info(f"получено публикаций: {len(pubs_list)}", "INFO")
                    
                    # отладка
                    if pubs_list:
                        self.logger.info(f"пример первой публикации: {pubs_list[0]}")
                    
                    self.current_publications = pubs_list
                    self.root.after(0, self._update_publications_display, pubs)
                else:
                    self.logger.error("не удалось загрузить публикации")

                # загружаем цитирования
                self.logger.info("загрузка цитирований...")
                refs = self.parser.get_author_refs(author_id)
                if refs:
                    self.logger.info(f"получено цитирований: {len(refs.get('refs', []))}")
                    self.current_refs = refs.get('refs', [])
                    self.root.after(0, self._update_refs_display, refs)
                else:
                    self.logger.error("не удалось загрузить цитирования")

                # обновляем статистику
                self.logger.info("обновление статистики...")
                self.root.after(0, self._update_stats)

            else:
                self.root.after(0, messagebox.showerror, "Ошибка", f"Автор с ID {author_id} не найден")
                self.root.after(0, self.status_label.config, {"text": "Ошибка"})
        
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Ошибка", str(e))
            self.root.after(0, self.status_label.config, {"text": "Ошибка"})
        finally:
            self.root.after(0, self.search_btn.config, {"state": tk.NORMAL})
    
    def _update_profile_display(self, profile):
        """Обновление отображения профиля"""
        if not profile:
            return
    
        self.fio_label.config(text=profile.get('full_name', '—'))
        self.org_label.config(text=profile.get('organization', '—'))
        self.spin_label.config(text=profile.get('spin_code', '—'))
        self.authorid_label.config(text=profile.get('author_id', '—'))
        
        self.pubs_total_label.config(text=str(profile.get('publications_total', 0)))
        self.pubs_risc_label.config(text=str(profile.get('publications_risc', 0)))
        self.cites_total_label.config(text=str(profile.get('citations_total', 0)))
        self.cites_risc_label.config(text=str(profile.get('citations_risc', 0)))
        self.h_index_label.config(text=str(profile.get('h_index_risc', 0)))
        self.h_index_self_label.config(text=str(profile.get('h_index_without_self', 0)))
        self.coauthors_label.config(text=str(profile.get('coauthors_count', 0)))
        self.first_year_label.config(text=str(profile.get('first_publication_year', '—')))

        # места работы
        if hasattr(self, 'org_detail_label'):
            positions = profile.get('positions', [])
            if positions:
                org_text = "\n".join([f"• {p.get('organization', '')} ({p.get('period', '')}) - {p.get('publications', '')} публ." 
                                    for p in positions])
                self.org_detail_label.config(text=org_text)
            else:
                self.org_detail_label.config(text="нет данных о местах работы")
    
    def _update_publications_display(self, pubs_data):
        """Обновление отображения публикаций"""
        # Очищаем таблицу
        for item in self.pubs_tree.get_children():
            self.pubs_tree.delete(item)
        
        pubs = pubs_data.get('publications', [])
        total = pubs_data.get('total_publications', len(pubs))
        self.pubs_info.config(text=f"Найдено публикаций: {total}")
        
        self.logger.info(f"получено {len(pubs)} публикаций для отображения", "INFO")
        
        for i, pub in enumerate(pubs, 1):
            # получаем данные с проверкой на None
            title = pub.get('title', '')
            if not title:
                title = pub.get('название', '')
            
            source = pub.get('source_info', '')
            if not source:
                source = pub.get('журнал', '')
                if not source:
                    source = pub.get('journal', '')
            
            year = pub.get('year', '')
            if not year:
                year = pub.get('год', '')
            
            citations = pub.get('citations', 0)
            if citations is None:
                citations = 0
            
            # обрезаем длинные строки для отображения
            if len(title) > 100:
                title = title[:100] + '...'
            if len(source) > 50:
                source = source[:50] + '...'
            
            # вставляем строку
            self.pubs_tree.insert('', tk.END, values=(
                i,
                title,
                source,
                year,
                citations
            ))
        
        self.logger.info(f"отображено {len(pubs)} публикаций")
    
    def _update_refs_display(self, refs_data):
        """Обновление отображения цитирований"""
        # Очищаем таблицу
        for item in self.refs_tree.get_children():
            self.refs_tree.delete(item)
        
        refs = refs_data.get('refs', [])
        self.refs_info.config(text=f"Найдено цитирований: {refs_data.get('total_refs', len(refs))}")
        
        for i, ref in enumerate(refs, 1):
            self.refs_tree.insert('', tk.END, values=(
                i,
                ref.get('cited_work', '')[:100],
                ref.get('source_title', '')[:100],
                ref.get('source_year', '')
            ))
    
    def _update_stats(self):
        """Обновление статистики"""
        pubs = self.current_publications
        
        if not pubs:
            self.logger.info("нет публикаций для статистики")
            # очищаем статистику
            self.stat_total_pubs.config(text="0")
            self.stat_total_cites.config(text="0")
            self.stat_avg_cites.config(text="0")
            self.top_title.config(text="—")
            self.top_info.config(text="")
            
            self.years_text.config(state=tk.NORMAL)
            self.years_text.delete(1.0, tk.END)
            self.years_text.insert(tk.END, "нет данных о публикациях")
            self.years_text.config(state=tk.DISABLED)
            return
        
        # отладка
        if pubs and len(pubs) > 0:
            self.logger.info(f"пример структуры публикации: {pubs[0]}")
            self.logger.info(f"ключи в публикации: {list(pubs[0].keys())}")

        # Основные показатели
        total_pubs = len(pubs)
        total_cites = sum(p.get('citations', 0) for p in pubs)
        avg_cites = total_cites / total_pubs if total_pubs > 0 else 0
        
        self.stat_total_pubs.config(text=str(total_pubs))
        self.stat_total_cites.config(text=str(total_cites))
        self.stat_avg_cites.config(text=f"{avg_cites:.2f}")
        
        # Самая цитируемая статья
        if pubs:
            top_pub = max(pubs, key=lambda x: x.get('citations', 0))
            if top_pub.get('citations', 0) > 0:
                self.top_title.config(text=top_pub.get('title', '—'))
                self.top_info.config(text=f"Цитирований: {top_pub.get('citations', 0)} | Год: {top_pub.get('year', '—')}")
        
        # Распределение по годам
        years = {}
        for pub in pubs:
            year = pub.get('year')
            if year:
                years[year] = years.get(year, 0) + 1
        
        if years:
            self.years_text.config(state=tk.NORMAL)
            self.years_text.delete(1.0, tk.END)
            
            for year in sorted(years.keys()):
                self.years_text.insert(tk.END, f"{year}: {'█' * years[year]} {years[year]} публикаций\n")
            
            self.years_text.config(state=tk.DISABLED)
        
        self.logger.info("статистика обновлена")
    
    def save_to_csv(self):
        """Сохранение данных в CSV"""
        if not self.current_profile:
            messagebox.showwarning("Предупреждение", "Нет данных для сохранения")
            return
        
        # Формируем имя файла
        author_id = self.current_author_id or 'unknown'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"author_{author_id}_{timestamp}.csv"
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # Записываем профиль
                writer.writerow(['=== ПРОФИЛЬ АВТОРА ==='])
                writer.writerow(['Параметр', 'Значение'])
                writer.writerow(['ФИО', self.current_profile.get('full_name', '')])
                writer.writerow(['Организация', self.current_profile.get('organization', '')])
                writer.writerow(['SPIN', self.current_profile.get('spin_code', '')])
                writer.writerow(['AuthorID', self.current_profile.get('author_id', '')])
                writer.writerow(['Индекс Хирша', self.current_profile.get('h_index_risc', 0)])
                writer.writerow(['Публикаций в РИНЦ', self.current_profile.get('publications_risc', 0)])
                writer.writerow(['Цитирований в РИНЦ', self.current_profile.get('citations_risc', 0)])
                writer.writerow([])
                
                # Записываем публикации
                if self.current_publications:
                    writer.writerow(['=== ПУБЛИКАЦИИ ==='])
                    writer.writerow(['№', 'Название', 'Источник', 'Год', 'Цитирований'])
                    for i, pub in enumerate(self.current_publications, 1):
                        writer.writerow([
                            i,
                            pub.get('title', ''),
                            pub.get('source_info', ''),
                            pub.get('year', ''),
                            pub.get('citations', 0)
                        ])
            
            messagebox.showinfo("Успешно", f"Данные сохранены в:\n{filepath}")
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить данные:\n{e}")
    
    def open_id_list(self):
        """Открыть файл со списком ID"""
        filepath = filedialog.askopenfilename(
            title="Выберите файл со списком ID",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filepath:
            messagebox.showinfo("Информация", f"Выбран файл:\n{filepath}\n\nФункция пакетной обработки будет добавлена позже.")
    
    def clear_results(self):
        """Очистка результатов"""
        self.current_profile = None
        self.current_publications = []
        self.current_refs = []
        
        # Очищаем профиль
        self.fio_label.config(text="—")
        self.org_label.config(text="—")
        self.spin_label.config(text="—")
        self.authorid_label.config(text="—")
        
        for attr in ['pubs_total', 'pubs_risc', 'cites_total', 'cites_risc', 
                     'h_index', 'h_index_self', 'coauthors', 'first_year']:
            getattr(self, attr + "_label").config(text="0")
        
        # Очищаем публикации
        for item in self.pubs_tree.get_children():
            self.pubs_tree.delete(item)
        self.pubs_info.config(text="Публикации не загружены")
        
        # Очищаем цитирования
        for item in self.refs_tree.get_children():
            self.refs_tree.delete(item)
        self.refs_info.config(text="Цитирования не загружены")
        
        # Очищаем статистику
        self.stat_total_pubs.config(text="0")
        self.stat_total_cites.config(text="0")
        self.stat_avg_cites.config(text="0")
        self.top_title.config(text="—")
        self.top_info.config(text="")
        
        self.years_text.config(state=tk.NORMAL)
        self.years_text.delete(1.0, tk.END)
        self.years_text.config(state=tk.DISABLED)
        
        self.status_label.config(text="Очищено")
    
    def _create_entry_context_menu(self):
        """Создание контекстного меню для поля ввода"""
        self.entry_menu = tk.Menu(self.root, tearoff=0)
        self.entry_menu.add_command(label="Вставить", command=self.paste_from_clipboard)
        self.entry_menu.add_command(label="Очистить", command=self.clear_entry)
        self.entry_menu.add_separator()
        self.entry_menu.add_command(label="Копировать", command=self.copy_from_entry)
        self.entry_menu.add_command(label="Вырезать", command=self.cut_from_entry)
        
        # Привязываем события
        self.id_entry.bind("<Button-3>", self.show_entry_menu)
        self.id_entry.bind("<Control-v>", lambda e: self.paste_from_clipboard())
        self.id_entry.bind("<Control-c>", lambda e: self.copy_from_entry())
        self.id_entry.bind("<Control-x>", lambda e: self.cut_from_entry())

    def show_entry_menu(self, event):
        """Показ контекстного меню"""
        try:
            self.entry_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.entry_menu.grab_release()

    def paste_from_clipboard(self):
        """Вставка из буфера обмена"""
        try:
            clipboard_text = self.root.clipboard_get()
            # Очищаем поле и вставляем текст
            self.id_entry.delete(0, tk.END)
            self.id_entry.insert(0, clipboard_text.strip())
            self.status_label.config(text="Вставлено из буфера обмена")
        except:
            messagebox.showwarning("Ошибка", "Не удалось вставить из буфера обмена")

    def copy_from_entry(self):
        """Копирование выделенного текста"""
        try:
            selected_text = self.id_entry.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
            self.status_label.config(text="Скопировано")
        except:
            # Если ничего не выделено, копируем всё
            text = self.id_entry.get()
            if text:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                self.status_label.config(text="Весь текст скопирован")
    
    def cut_from_entry(self):
        """Вырезание выделенного текста"""
        try:
            selected_text = self.id_entry.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
            self.id_entry.delete(self.id_entry.index(tk.SEL_FIRST), self.id_entry.index(tk.SEL_LAST))
            self.status_label.config(text="Вырезано")
        except:
            pass

    def on_closing(self):
        """действия при закрытии окна"""
        print("закрытие приложения...")
        if hasattr(self, 'parser') and self.parser.authenticated:
            self.parser.logout()
        self.root.destroy()
    
    def clear_entry(self):
        """Очистка поля ввода"""
        self.id_entry.delete(0, tk.END)
        self.status_label.config(text="Поле очищено")

    def reauthenticate(self):
        """повторная авторизация"""
        
        # проверяем, есть ли уже браузер
        if hasattr(self.parser, 'requester') and self.parser.requester.driver:
            # спрашиваем подтверждение
            if not messagebox.askyesno("Подтверждение", 
                                    "Будет закрыт текущий браузер и открыт новый для повторного входа.\n"
                                    "После прохождения теста Тьюринга нажмите ОК в диалоговом окне.\n\n"
                                    "Продолжить?"):
                return
            
            # закрываем старую сессию
            try:
                self.parser.requester.driver.quit()
            except:
                pass
            self.parser.requester.driver = None
            self.parser.authenticated = False
        
        self.status_label.config(text="повторная авторизация...")
        self.logger.info("запуск повторной авторизации...", "INFO")
        
        # запускаем в отдельном потоке
        thread = threading.Thread(target=self._reauthenticate_thread)
        thread.daemon = True
        thread.start()

    def _reauthenticate_thread(self):
        """поток для повторной авторизации"""
        try:
            # получаем данные для входа
            from config import USE_LOGIN_FROM_CONFIG, LOGIN_DATA
            
            if USE_LOGIN_FROM_CONFIG:
                login = LOGIN_DATA.get('login')
                password = LOGIN_DATA.get('password')
            else:
                # если нужно, можно запросить ввод
                self.root.after(0, lambda: self.status_label.config(text="введите логин/пароль в консоли"))
                login = input("введите логин: ")
                password = input("введите пароль: ")
            
            # выполняем вход
            success = self.parser.authenticate(login, password, show_browser=True)
            
            if success:
                self.root.after(0, lambda: self.status_label.config(text="авторизация успешна"))
                self.root.after(0, lambda: self.logger.info("повторная авторизация успешна"))
                self.root.after(0, lambda: messagebox.showinfo("Успешно", "Повторный вход выполнен"))
            else:
                self.root.after(0, lambda: self.status_label.config(text="ошибка авторизации"))
                self.root.after(0, lambda: self.logger.info("ошибка повторной авторизации"))
                self.root.after(0, lambda: messagebox.showerror("Ошибка", "Не удалось выполнить повторный вход"))
                
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text="ошибка"))
            self.root.after(0, lambda: self.logger.info(f"ошибка: {e}"))

    def run(self):
        """Запуск приложения"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()