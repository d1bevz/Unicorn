import re  # Работа с регулярными выражениями
import pandas as pd
import string
import numpy as np
from rutermextract import TermExtractor
from fuzzywuzzy import fuzz


# Список размеченных профессий
PRELOAD_PROFESSIONS = ['Менеджер по продажам', "Продавец"]
PRELOAD_PROFESSIONS_FILE_NAME = {
    'Менеджер по продажам': 'set_of_sales_manager_skills.csv',
    'Продавец': 'set_of_seller_skills.csv'
}


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
        self.keywords.update(keywords)
        return self

    def find_skill(self, resume_key_words):
        """Функция проверяет схожесть ключевых слов по мере расстояния левенштайна и если находит хоть одно выше заданного threshold возвращает True
        resume_key_words - это датафрейм с ключевыми словами из текста описания, получается функцией get_key_words_list"""
        threshold = 90
        if len(resume_key_words)==None: return False  # Проверка на то, что ключевые слова были переданы    
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
    last_text_key_words = None

    def __init__(self, name, experience, skills = None):
        """Конструктор класса Position
        name - название позиции
        experience - опыт работы
        skills - список объектов
        """

        self.name = name
        self.experience = experience
        if not skills == None:
            self.skills = skills

        print(
            f'Позиция "{self.name}" успешно создана. Опыт {experience}. Ключевые навыки: {["".join(str(x.name)) for x in self.skills]}')

    def add_skills(self, skills):
        """Функция добавляет в текущий объект новые навыки"""
        self.skills.append(skills)
        return self

    def get_list_skills(self, text):
        """Функция из записи получает список ключевых навыков
        Результат будет сохранен в переменной last_text_key_words"""
        self.last_text_key_words = get_key_words_list(text)
        return self.last_text_key_words

    def check_experience(self):
        """Функция возвращает условия фильтрация по опыту"""

        return {
            'noExperience': (lambda x: x < 1),
            'between1And3': (lambda x: x >= 1 and x <= 3),
            'between3And6': (lambda x: x >= 3 and x <= 6),
            'moreThan6': (lambda x: x > 6)
        }[self.experience]
    
    def check_skills(self, text=None):
        """Функция проверяет наличие навыков в текстовом описание кандидата, либо в списке ключевых слов. 
        По умолчанию использует последний проанализированный текст, если была проверка до этого"""      
        if text!=None:
            key_words=self.get_list_skills(text)
        else:
            key_words=self.last_text_key_words
        if text==None and key_words==None:
            raise TypeError
        result = {}
        for skill in self.skills:
            result[skill.name] = skill.find_skill(key_words)
        return result
    
    
