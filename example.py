from Unicorn import load_markedup_profession, make_keywords_dict, Skill, Position  # Выгрузка размеченных данных
from Unicorn import PRELOAD_PROFESSIONS

# Берем размеченные навыки для Менеджера по продажам
# Для удобства = они хранятся в датафрейме
skills_raw =  load_markedup_profession(PRELOAD_PROFESSIONS[0])
skills_list = skills_raw.index.drop_duplicates().to_list()

# Создаем объекты навыкина все выбранные навыки
# Объекты будут определять факт наличия у кандидата навыка
skills_list = skills_raw.index.drop_duplicates().to_list()
skills_objects = []
for skill in skills_list:
    # В цикле собираем все объекты навыков в одну группу
    skill_keywords = make_keywords_dict(skills_raw.loc[skill, 'keywords'])
    skill_kind = skills_raw.loc[skill, 'kind']
    skill_kind = skill_kind if type(skill_kind)==str else skill_kind.unique()
    
    skills_objects.append(
        Skill(name=skill, kind=skill_kind, keywords=skill_keywords)
    )
    
# Далее все объекты навыков можно привязать к объекту позиции
# Создание объекта "менеджер по продажам"
sales_manager = Position(name=PRELOAD_PROFESSIONS[0], experience='between3And6', skills=skills_objects)

# Данный объект парсит из текста 
# Например возьмем датасет из примера к заданию
resumes = pd.read_csv('resume_train.csv', delimiter=';', encoding='utf-8')

# Отфильтруем только нужную позицию
def filter_by_position(data, position_pattern):
    """Функция фильтрует по названию профессии и возвращает индексы совпавших с паттерном строк
    data - это массив данных
    position_pattern - это паттерн позиции, который мы ищем, объект Re"""
    result = data.str.lower().str.contains(pattern)
    return result
    
    
# Сохраняем только сейлз менеджеров
pattern = re.compile('(менеджер по продажам|sales manager|сейлз-менеджер)')  # Задаются три группы схожести названия должности
resumes_sales_managers = resumes.dropna().copy()
resumes_sales_managers = resumes_sales_managers.loc[filter_by_position(resumes.position, pattern)]


# Из отфильтрованных резюме парсим данные о скиллах
result = resumes_sales_managers.head(10).description.map(sales_manager.check_skills).apply(pd.Series)
result
