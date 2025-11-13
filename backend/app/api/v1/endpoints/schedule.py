"""
Управление расписанием
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.db.session import get_db
from app.schemas.schedule import LessonRead, SchedulePatch, ScheduleChangelogRead
from app.services.schedule_service import (
    get_schedule_for_group,
    get_schedule_for_teacher,
    patch_schedule,
    get_schedule_changelog,
)
from app.models.lesson_group import LessonGroup
from app.models.user import User
from app.models.room import Room
from app.models.subject import Subject
from app.models.student_group import StudentGroup
from app.models.timeslot import Timeslot
import uuid

router = APIRouter()


@router.get(
    "",
    response_model=List[LessonRead],
    summary="Получение расписания",
    description="Получает расписание для группы или преподавателя. Можно указать week_start для фильтрации по неделе.",
)
def get_schedule(
    group_id: uuid.UUID | None = None,
    teacher_user_id: uuid.UUID | None = None,
    week_start: Optional[date] = None,
    db: Session = Depends(get_db),
) -> List[LessonRead]:
    """
    Получение расписания
    
    Возвращает расписание для указанной группы или преподавателя.
    Можно указать week_start для фильтрации по неделе (формат: YYYY-MM-DD).
    Расписание создается пустым при добавлении факультета, дальше только патчи.
    """
    if not group_id and not teacher_user_id:
        raise HTTPException(status_code=400, detail="Необходимо указать group_id или teacher_user_id")
    
    if group_id:
        lessons = get_schedule_for_group(db=db, group_id=group_id, week_start=week_start)
    elif teacher_user_id:
        lessons = get_schedule_for_teacher(db=db, teacher_user_id=teacher_user_id, week_start=week_start)
    else:
        lessons = []
    
    # Преобразуем уроки в формат с полной информацией
    result = []
    for lesson in lessons:
        # Получаем полную информацию о преподавателе
        teacher = db.get(User, lesson.teacher_user_id)
        teacher_name = teacher.full_name if teacher else "Неизвестно"
        
        # Получаем полную информацию об аудитории
        room = db.get(Room, lesson.room_id)
        room_name = f"ауд {room.number}" if room else "Неизвестно"
        if room and room.building:
            room_name = f"{room_name} ({room.building})"
        
        # Получаем полную информацию о предмете
        subject = db.get(Subject, lesson.subject_id)
        subject_name = subject.title if subject else "Неизвестно"
        
        # Получаем группы для урока
        lesson_groups = db.query(LessonGroup).filter(LessonGroup.lesson_id == lesson.id).all()
        group_names = []
        for lg in lesson_groups:
            group = db.get(StudentGroup, lg.group_id)
            if group:
                group_names.append(group.name)
        
        # Получаем время из timeslot
        timeslot = db.get(Timeslot, lesson.pair_no)
        time_str = None
        if timeslot:
            start_str = timeslot.start.strftime("%H:%M")
            end_str = timeslot.end.strftime("%H:%M")
            time_str = f"{start_str} - {end_str}"
        
        result.append(LessonRead(
            id=lesson.id,
            teacher=teacher_name,
            room=room_name,
            subject=subject_name,
            pair_no=lesson.pair_no,
            groups=group_names,
            time=time_str,
        ))
    
    return result


@router.patch(
    "/patch",
    summary="Применение патчей к расписанию",
    description="Применяет изменения (патчи) к расписанию. "
                "Записывает изменения в журнал и обновляет версию расписания.",
)
def patch_schedule_endpoint(
    patches: List[SchedulePatch],
    group_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
):
    """
    Применение патчей к расписанию
    
    Применяет изменения к расписанию:
    - Создает записи в Schedule changelog
    - Обновляет версию расписания
    - Отправляет уведомления пользователям, связанным с изменением
    """
    try:
        results = patch_schedule(db=db, patches=patches, group_id=group_id)
        return {
            "success": True,
            "results": results,
            "message": "Патчи применены успешно"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при применении патчей: {str(e)}")


@router.get(
    "/changelog",
    response_model=List[ScheduleChangelogRead],
    summary="Журнал изменений расписания",
    description="Получает журнал изменений расписания для группы или преподавателя.",
)
def get_schedule_changelog_endpoint(
    group_id: uuid.UUID | None = None,
    teacher_user_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
) -> List[ScheduleChangelogRead]:
    """Получить журнал изменений расписания"""
    changelogs = get_schedule_changelog(db=db, group_id=group_id, teacher_user_id=teacher_user_id)
    return [ScheduleChangelogRead.model_validate(changelog) for changelog in changelogs]

