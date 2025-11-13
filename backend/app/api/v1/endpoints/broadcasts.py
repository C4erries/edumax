"""
Рассылки от преподавателей
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.broadcast import BroadcastCreate, BroadcastRead
from app.services.broadcast_service import (
    get_broadcast_by_id,
    get_broadcasts_for_user,
    get_broadcasts_for_group,
    get_teacher_broadcasts,
    create_broadcast,
)
from app.api.deps import get_current_active_user

router = APIRouter()


@router.get("", response_model=List[BroadcastRead], summary="Получить рассылки")
def get_broadcasts(
    group_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[BroadcastRead]:
    """
    Получить рассылки для пользователя
    
    Для студентов: возвращает рассылки для их группы/факультета
    Для преподавателей: можно указать group_id для получения рассылок конкретной группы
    """
    if group_id:
        broadcasts = get_broadcasts_for_group(db, group_id)
    elif current_user.role == UserRole.STUDENT:
        broadcasts = get_broadcasts_for_user(db, current_user.id)
    else:
        # Для преподавателей/админов без указания группы - возвращаем пустой список
        broadcasts = []
    
    result = []
    for broadcast in broadcasts:
        broadcast_dict = BroadcastRead.model_validate(broadcast).model_dump()
        
        # Добавляем имена
        if broadcast.author:
            broadcast_dict["author_full_name"] = broadcast.author.full_name
        if broadcast.group:
            broadcast_dict["group_name"] = broadcast.group.name
        if broadcast.faculty:
            broadcast_dict["faculty_name"] = broadcast.faculty.name
        
        result.append(BroadcastRead(**broadcast_dict))
    
    return result


@router.get("/my", response_model=List[BroadcastRead], summary="Мои рассылки")
def get_my_broadcasts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[BroadcastRead]:
    """Получить все рассылки, созданные текущим преподавателем"""
    if current_user.role not in [UserRole.STAFF, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступно только для преподавателей и администраторов"
        )
    
    broadcasts = get_teacher_broadcasts(db, current_user.id)
    
    result = []
    for broadcast in broadcasts:
        broadcast_dict = BroadcastRead.model_validate(broadcast).model_dump()
        
        # Добавляем имена
        if broadcast.author:
            broadcast_dict["author_full_name"] = broadcast.author.full_name
        if broadcast.group:
            broadcast_dict["group_name"] = broadcast.group.name
        if broadcast.faculty:
            broadcast_dict["faculty_name"] = broadcast.faculty.name
        
        result.append(BroadcastRead(**broadcast_dict))
    
    return result


@router.get("/{broadcast_id}", response_model=BroadcastRead, summary="Детали рассылки")
def get_broadcast_details(
    broadcast_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> BroadcastRead:
    """Получить детальную информацию о рассылке"""
    broadcast = get_broadcast_by_id(db, broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рассылка не найдена")
    
    broadcast_dict = BroadcastRead.model_validate(broadcast).model_dump()
    
    # Добавляем имена
    if broadcast.author:
        broadcast_dict["author_full_name"] = broadcast.author.full_name
    if broadcast.group:
        broadcast_dict["group_name"] = broadcast.group.name
    if broadcast.faculty:
        broadcast_dict["faculty_name"] = broadcast.faculty.name
    
    return BroadcastRead(**broadcast_dict)


@router.post("", response_model=BroadcastRead, status_code=status.HTTP_201_CREATED, summary="Создать рассылку")
def create_broadcast_endpoint(
    broadcast_data: BroadcastCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> BroadcastRead:
    """Создать новую рассылку (только для преподавателей и администраторов)"""
    try:
        broadcast = create_broadcast(db, broadcast_data=broadcast_data, author_user_id=current_user.id)
        
        broadcast_dict = BroadcastRead.model_validate(broadcast).model_dump()
        
        # Добавляем имена
        if broadcast.author:
            broadcast_dict["author_full_name"] = broadcast.author.full_name
        if broadcast.group:
            broadcast_dict["group_name"] = broadcast.group.name
        if broadcast.faculty:
            broadcast_dict["faculty_name"] = broadcast.faculty.name
        
        return BroadcastRead(**broadcast_dict)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

