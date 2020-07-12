from Unicorn import load_markedup_profession, make_keywords_dict, Skill  # Выгрузка размеченных данных


# Берем навыки для Менеджера по продажам    
skills_raw =  load_markedup_profession('Продавец')
skills_list = skills_raw.index.drop_duplicates().to_list()

# Создаем парсер на все выбранные скилы
skills_list = skills_raw.index.drop_duplicates().to_list()
skills_objects = []
for skill in skills_list:
    # В цикле собираем все объекты навыков
    skill_keywords = make_keywords_dict(skills_raw.loc[skill, 'keywords'])
    skill_kind = skills_raw.loc[skill, 'kind']
    skill_kind = skill_kind if type(skill_kind)==str else skill_kind.unique()
    
    skills_objects.append(
        Skill(name=skill, kind=skill_kind, keywords=skill_keywords)
    )

