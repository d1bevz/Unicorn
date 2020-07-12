import re  # Работа с регулярными выражениями
import pandas as pd
import string
import numpy as np
import nltk
nltk.download("stopwords")
#--------#
from nltk.corpus import stopwords
from pymystem3 import Mystem
from string import punctuation
from rutermextract import TermExtractor
from fuzzywuzzy import fuzz


#Create lemmatizer and stopwords list
mystem = Mystem() 
russian_stopwords = stopwords.words("russian")

# Список размеченных профессий
PRELOAD_PROFESSIONS = ['Менеджер по продажам', "Продавец"]
PRELOAD_PROFESSIONS_FILE_NAME = {
    'Менеджер по продажам': 'set_of_sales_manager_skills.csv',
    'Продавец': 'set_of_seller_skills.csv'
}



def preprocess_text(text):
    """Функция делает предобработку текста"""
    tokens = mystem.lemmatize(text.lower())
    tokens = [token for token in tokens if token not in russian_stopwords \
              and token != " " \
              and token.strip() not in punctuation]
    text = " ".join(tokens)
    return text

def filter_by_position(data, position_pattern):
    """Функция фильтрует по названию профессии и возвращает индексы совпавших с паттерном строк
    data - это массив данных
    position_pattern - это паттерн позиции, который мы ищем, объект Re"""
    result = data.str.lower().str.contains(pattern)
    return result

def get_key_words_list(text):
    """Получает из текста список всех ключевых слов"""
    # Проходим извлекателем ключевых слов
    term_extractor = TermExtractor()
    terms = term_extractor(text)
    # структура датафрейма
    dataframe_structure = {
        'key_word': []
        , 'count': []
    }
    for term in terms:
        dataframe_structure['key_word'].append(term.normalized)
        dataframe_structure['count'].append(term.count)
    
    result = pd.DataFrame(dataframe_structure)
    return result

def load_markedup_profession(profession):
    """Функция возвращает предустановленную разметку для Менеджера по продажам"""
    if profession in PRELOAD_PROFESSIONS:        
        result = pd.read_csv(PRELOAD_PROFESSIONS_FILE_NAME[profession], sep=';')
        return result.set_index('name')

def make_keywords_dict(keywords):
    """Функция возвращает словарь со всеми паттернами из ключевых слов"""
    
    result = {}
    if type(keywords)==str:
        return {keywords:re.compile(keywords)}
    for keyword in keywords:
        result[keyword] = re.compile(keyword)
    return result 

class Skill:
    name = ''
    kind = ''
    keywords = {}

    def __init__(self, name, kind, keywords=None):
        """Функция создает новый объект класса Навык
        name - название навыка
        kind - тип навыка (опыт, hard skill, soft skill)
        keywords - список синонимов, представленных в виде словаря {ключевое слово: регулярное выражение re.Pattern}
        Возвращает текущий объект"""

        self.name = name
        self.kind = kind
        if (keywords == None):
            self.keywords = {name: re.compile(name)}
        else:
            self.keywords = keywords

        print(
            f'Навык "{self.name}" успешно добавлен. Тип: {self.kind}. Ключевые слова: {["".join(str(x)) for x in self.keywords.keys()]}')
        return None

    def add_keywords(self, keywords):
        """Функция добавляет в текущий объект новые ключевые слова
        keywords - это словарь {ключевое слово: регулярное выражение re.Pattern}"""
        if self.keywords == None:
            self.keywords = {}
        self.keywords.update(keywords)
        return self

    def find_skill(self, resume_key_words):
        """Функция проверяет схожесть ключевых слов по мере расстояния левенштайна и если находит хоть одно выше заданного threshold возвращает True
        resume_key_words - это датафрейм с ключевыми словами из текста описания, получается функцией get_key_words_list"""
        threshold = 90
        result = resume_key_words.copy()
        
        simularity = lambda x, key_word: fuzz.partial_ratio(x, key_word)
        
        for keyword in self.keywords.keys():
            result[keyword] = result['key_word'].apply(simularity, key_word=keyword)
            result[keyword] = result[keyword][result[keyword] >= threshold]
        
        
        result['match'] = result.loc[:, self.keywords.keys()].sum(axis=1)
        
        result = result.sort_values('match', ascending=False)
        #return result
        if result['match'].sum() > 0:
            return True
        else: return False


class Position:
    name = ''
    experience = ''
    skills = []

    def __init__(self, name, experience, skills = None):
        """Конструктор класса Vacancy
        vacancy - запись вакансии
        Создает объект Vacancy на основе записи
        """

        self.name = name
        self.experience = experience
        self.skills = skills

        print(
            f'Вакансия "{self.name}" успешно создана. Опыт {experience}. Ключевые навыки: {["".join(str(x.name)) for x in self.skills]}')


    def add_skills(self, skills):
        """Функция добавляет в текущий объект новые навыки"""
        if self.skills == None:
            self.skills = {}
        self.skills.update(skills)
        return self


    def get_list_skills(self, vacancy):
        """Функция из записи получает список ключевых навыков"""

        # Получаем ключевые слова
        term_extractor = TermExtractor()
        skills = [term.normalized for term in term_extractor(vacancy['description'], limit=10)]

        # Если присуствует запись 'key_skills' от из нее извлекаем ключевые навыки
        # и добавляем к другим навыкам полученным через rutermextract
        if (not pd.isnull(vacancy['key_skills'])):
            skills = list(set(skills) | set(vacancy['key_skills'].lower().split(' | ')))  # Убираем совпадения

        return skills;

    def check_experience(self):
        """Функция возвращает условия фильтрация по опыту"""

        return {
            'noExperience': (lambda x: x < 1),
            'between1And3': (lambda x: x >= 1 and x <= 3),
            'between3And6': (lambda x: x >= 3 and x <= 6),
            'moreThan6': (lambda x: x > 6)
        }[self.experience]

    def get_vacancies(self, df):
        """Метод возвращает отфильтрованные вакансии"""

        # Фильтрация по опыту
        df = df[df.experience.apply(self.check_experience())]

        # Установка флагов по скиллам
        for skill in self.skills:
            df[skill.name] = df.description.apply(skill.find_skill)

        # Расчет спидометра
        skill_names = [x.name for x in self.skills]
        df.insert(0, 'Спидометр', df[skill_names].sum(axis=1))

        # Возращает топ 10 кандидатов
        return df.sort_values(['Спидометр', 'experience'], ascending=False).head(10)
