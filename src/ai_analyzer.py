# src/ai_analyzer.py
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import logging
import re
from collections import Counter

class AIAnalyzer:
    """анализатор для извлечения тем и ключевых слов из публикаций"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.stop_words = ['для', 'и', 'в', 'на', 'с', 'по', 'от', 'это', 'его', 'ее', 'их', 'что', 'как', 'к', 'у']
    
    def extract_keywords(self, publications, top_n=10):
        """
        Извлечение ключевых слов из названий публикаций методом TF-IDF
        """
        if not publications:
            return []
        
        # собираем все названия
        texts = [p.get('title', '') for p in publications if p.get('title')]
        if len(texts) < 2:
            return []
        
        try:
            # создаем векторизатор
            vectorizer = TfidfVectorizer(
                max_features=50,
                stop_words=self.stop_words,
                min_df=1,
                max_df=0.8
            )
            
            # преобразуем тексты в матрицу TF-IDF
            X = vectorizer.fit_transform(texts)
            
            # суммируем веса по всем документам
            avg_tfidf = np.array(X.mean(axis=0)).flatten()
            
            # получаем топ-N слов
            top_indices = avg_tfidf.argsort()[-top_n:][::-1]
            feature_names = vectorizer.get_feature_names_out()
            
            keywords = []
            for idx in top_indices:
                if avg_tfidf[idx] > 0.01:  # отсекаем слишком редкие
                    keywords.append({
                        'word': feature_names[idx],
                        'weight': round(float(avg_tfidf[idx]), 3)
                    })
            
            return keywords
            
        except Exception as e:
            self.logger.error(f"ошибка при извлечении ключевых слов: {e}")
            return []
    
    def extract_topics(self, publications, min_frequency=2):
        """
        Простой частотный анализ слов для определения тем
        """
        if not publications:
            return []
        
        # объединяем все названия
        all_text = ' '.join([p.get('title', '') for p in publications if p.get('title')])
        
        # очищаем текст
        all_text = all_text.lower()
        # убираем пунктуацию
        all_text = re.sub(r'[^\w\s]', ' ', all_text)
        
        # разбиваем на слова
        words = all_text.split()
        
        # фильтруем короткие слова и стоп-слова
        words = [w for w in words if len(w) > 3 and w not in self.stop_words]
        
        # считаем частоту
        word_counts = Counter(words)
        
        # возвращаем топ-20
        return word_counts.most_common(20)
    
    def analyze_author_interests(self, publications):
        """
        Комплексный анализ интересов автора
        """
        result = {
            'keywords_tfidf': self.extract_keywords(publications, 15),
            'frequent_words': self.extract_topics(publications),
            'total_analyzed': len(publications),
            'main_topics': []
        }
        
        # формируем основные темы на основе ключевых слов
        if result['keywords_tfidf']:
            result['main_topics'] = [kw['word'] for kw in result['keywords_tfidf'][:5]]
        
        return result