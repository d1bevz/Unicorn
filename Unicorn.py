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
        # Проверки на входе, что правильный тип данных
        # ДОПИСАТЬСЯ
        pass
        return self

    def find_skill(self, text):
        """Функция ищет упоминания навыка в тексте
        text - это текст, в котором необходимо найти упоминание навыка"""
        if (not pd.isnull(text)):
            for keyword in self.keywords.keys():
                result = re.findall(keyword, text.lower())
                if len(result) > 0:
                    return True
        return False


class Vacancy:
    name = ''
    name_pattern = ''
    experience = ''
    skills = []

    def __init__(self, vacancy):
        """Конструктор класса Vacancy
        vacancy - запись вакансии
        Создает объект Vacancy на основе записи
        """

        term_extractor = TermExtractor()

        self.name = vacancy['name.lemm']
        self.name_pattern = re.compile("|".join([term.normalized for term in term_extractor(self.name, limit=10)]))
        self.experience = vacancy['experience']
        self.skills = [Skill(skill, 'skill') for skill in self.get_list_skills(vacancy)]

        experience_name = vacancy['experience.name']

        print(
            f'Вакансия "{self.name}" успешно создана. Опыт {experience_name}. Ключевые навыки: {["".join(str(x.name)) for x in self.skills]}')

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
        return {
            'noExperience': (lambda x: x < 1),
            'between1And3': (lambda x: x >= 1 and x <= 3),
            'between3And6': (lambda x: x >= 3 and x <= 6),
            'moreThan6': (lambda x: x > 6)
        }[self.experience]

    def get_vacancies(self, df):
        """Метод возвращает отфильтрованные вакансии"""

        # Фильтрация по позиции
        df = df.loc[df.position.str.lower().str.contains(self.name_pattern)].dropna()

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

