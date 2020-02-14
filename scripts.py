import random
import logging
import textwrap

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

from datacenter.models import Commendation, Subject, Lesson, Schoolkid, Mark, Chastisement

COMMENDATIONS = """\
    Молодец!
    Отлично!
    Хорошо!
    Гораздо лучше, чем я ожидал!
    Ты меня приятно удивил!
    Великолепно!
    Прекрасно!
    Ты меня очень обрадовал!
    Именно этого я давно ждал от тебя!
    Сказано здорово – просто и ясно!
    Ты, как всегда, точен!
    Очень хороший ответ!
    Талантливо!
    Ты сегодня прыгнул выше головы!
    Я поражен!
    Уже существенно лучше!
    Потрясающе!
    Замечательно!
    Прекрасное начало!
    Так держать!
    Ты на верном пути!
    Здорово!
    Это как раз то, что нужно!
    Я тобой горжусь!
    С каждым разом у тебя получается всё лучше!
    Мы с тобой не зря поработали!
    Я вижу, как ты стараешься!
    Ты растешь над собой!
    Ты многое сделал, я это вижу!
    Теперь у тебя точно все получится!"""


def get_random_commendation():
    return random.choice([row.strip() for row in textwrap.dedent(COMMENDATIONS).strip().split('\n')])


def fix_marks(schoolkid: Schoolkid):
    """Исправляет оценки ниже или равные 3 на 5."""
    Mark.objects.filter(schoolkid=schoolkid, points__lte=3).update(points=5)


def remove_chastisements(schoolkid: Schoolkid):
    """Удаляет замечения определённого ученика."""
    Chastisement.objects.filter(schoolkid=schoolkid).delete()


def get_schoolkid_entity(full_name):
    """Получаем объект ученика для дальнейших манипуляций."""
    try:
        return Schoolkid.objects.get(full_name__contains=full_name)
    except ObjectDoesNotExist:
        logging.error(f"По условнию поиска <<{full_name}>> в базе ничего не найдено. Проверьте условие поиска")
    except MultipleObjectsReturned:
        logging.error(
            f"С условием поиска <<{full_name}>> найдено не сколько объектов. "
            f"По-пробуйте уточнить поиск добавив имя или отчество")


def create_commendation(user_lastname_name: str, subject: str, commendation_text: str = None):
    """Добавим похвалу ученику. Похвала может генерироваться автоматически."""
    schoolkid = get_schoolkid_entity(user_lastname_name)
    try:
        required_subject = Subject.objects.get(title__iexact=subject, year_of_study=schoolkid.year_of_study)
    except ObjectDoesNotExist:
        logging.error(f"Предмета <<{subject}>> для {schoolkid.year_of_study} года обучения не существует")
    except MultipleObjectsReturned:
        logging.error(f"Уточните название предмета <<{subject}>> или прооверьте базу на дубликаты")

    # здесь нам нужен только последний результат LIMIT 1
    last_lesson = Lesson.objects.filter(subject=required_subject,
                                        group_letter=schoolkid.group_letter,
                                        year_of_study=schoolkid.year_of_study
                                        ).order_by('-date')[0]

    commendation = Commendation(created=last_lesson.date,
                                schoolkid=schoolkid,
                                subject=required_subject,
                                teacher=last_lesson.teacher,
                                text=commendation_text or get_random_commendation()
                                )
    commendation.save()
