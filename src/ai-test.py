from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from typing import List, Literal, Optional, Dict, Any

import requests
from pydantic import BaseModel, ValidationError, Field

# ==========================
# CONFIG
# ==========================

OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_NAME = "openai/gpt-4o-mini"
TEMPERATURE = 0.2
MAX_RETRIES = 3
TIMEOUT = 30


# ==========================
# DATA MODELS
# ==========================

class CognitiveAnalysisResult(BaseModel):
    concentration_level: Literal["deep", "medium", "light"]
    confidence: float = Field(ge=0.0, le=1.0)
    recommended_block_minutes: int = Field(ge=5, le=240)
    preferred_energy: Literal["high", "medium", "low"]
    reason: str
    actions: List[str]


class SchedulingResult(BaseModel):
    """Результат планирования времени"""
    is_scheduled: bool
    slot: Optional[Dict[str, datetime]] = None
    message: str
    quality: Literal["optimal", "good", "acceptable", "poor", "impossible"]
    peak_period: Optional[str] = None
    deadline_met: Optional[bool] = None
    time_until_deadline: Optional[str] = None


class TaskInput(BaseModel):
    title: str
    description: str
    tags: Optional[List[str]] = None
    user_estimate: Optional[str] = None
    deadline: Optional[str] = None
    free_time_slots: Optional[List[Dict[str, str]]] = None
    sleep_schedule: Optional[Dict[str, str]] = None


class TimeSlot(BaseModel):
    started_at: datetime
    ended_at: datetime


# ==========================
# PROMPTS
# ==========================

SYSTEM_PROMPT = """
Ты — интеллектуальный планировщик задач, который анализирует когнитивную сложность задач 
и оптимальное время для их выполнения на основе биоритмов человека.

АНАЛИЗИРУЙ СЛЕДУЮЩЕЕ:
1. Описание задачи и её теги
2. Расписание сна пользователя (когда встает и ложится)
3. Дедлайн задачи (если указан)

ВОЗВРАЩАЙ ТОЛЬКО JSON БЕЗ ЛЮБЫХ КОММЕНТАРИЕВ:
{
  "concentration_level": "deep|medium|light",
  "confidence": число_от_0_до_1,
  "recommended_block_minutes": число_от_5_до_240,
  "preferred_energy": "high|medium|low",
  "reason": "объяснение на русском с учетом расписания сна",
  "actions": ["действие1", "действие2"]
}
""".strip()


def build_user_prompt(task: TaskInput) -> str:
    """Строит промпт для ИИ с учетом всех данных"""

    prompt_parts = [
        "ЗАДАЧА ДЛЯ АНАЛИЗА:",
        f"НАЗВАНИЕ: {task.title}",
        f"ОПИСАНИЕ: {task.description}"
    ]

    if task.tags:
        tags_str = ", ".join(task.tags)
        prompt_parts.append(f"ТЕГИ: {tags_str}")

    if task.user_estimate:
        prompt_parts.append(f"ОЦЕНКА ПОЛЬЗОВАТЕЛЯ: {task.user_estimate}")

    if task.deadline:
        prompt_parts.append(f"ДЕДЛАЙН: {task.deadline}")

    if task.sleep_schedule:
        wake_up = task.sleep_schedule.get('wake_up_time', 'не указано')
        bed_time = task.sleep_schedule.get('bed_time', 'не указано')
        prompt_parts.append(f"РАСПИСАНИЕ СНА: просыпаюсь в {wake_up}, ложусь спать в {bed_time}")

    if task.free_time_slots:
        prompt_parts.append("\nСВОБОДНЫЕ ОКНА ВРЕМЕНИ:")
        for i, slot in enumerate(task.free_time_slots, 1):
            prompt_parts.append(f"{i}. {slot.get('started_at', '')} - {slot.get('ended_at', '')}")

    return "\n".join(prompt_parts)


# ==========================
# CORE LOGIC
# ==========================

def call_openrouter(system_prompt: str, user_prompt: str) -> str:
    """Вызов OpenRouter API"""
    payload = {
        "model": MODEL_NAME,
        "temperature": TEMPERATURE,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "cognitive-planner",
    }

    response = requests.post(
        OPENROUTER_URL,
        json=payload,
        headers=headers,
        timeout=TIMEOUT,
    )

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def analyze_task(task: TaskInput) -> CognitiveAnalysisResult:
    """Анализ задачи с помощью ИИ"""
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw_content = call_openrouter(
                SYSTEM_PROMPT,
                build_user_prompt(task),
            )

            parsed_json = json.loads(raw_content)
            return CognitiveAnalysisResult.model_validate(parsed_json)

        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            time.sleep(0.5 * attempt)

    raise RuntimeError(
        f"Не удалось получить валидный ответ от модели после {MAX_RETRIES} попыток"
    ) from last_error


# ==========================
# SCHEDULING LOGIC
# ==========================

def calculate_productivity_periods(
    wake_up_time: str,
    bed_time: str,
    task_type: str
) -> List[Dict[str, Any]]:
    """Рассчитывает периоды продуктивности на основе сна"""

    try:
        # Парсим время
        wake_up = datetime.strptime(wake_up_time, "%H:%M").time()
        bed = datetime.strptime(bed_time, "%H:%M").time()

        today = datetime.now().date()
        wake_up_dt = datetime.combine(today, wake_up)
        bed_dt = datetime.combine(today, bed)

        if bed_dt < wake_up_dt:
            bed_dt += timedelta(days=1)

        periods = []

        if task_type == "deep":
            # Утренний пик для глубокой работы
            morning_peak_start = wake_up_dt + timedelta(hours=1.5)
            morning_peak_end = wake_up_dt + timedelta(hours=4)

            periods.append({
                "name": "Утренний пик продуктивности",
                "description": "Идеальное время для глубокой концентрации",
                "start": morning_peak_start,
                "end": morning_peak_end,
                "priority": "optimal",
                "reason": "Через 1.5-4 часа после пробуждения, когда ум наиболее ясный"
            })

        elif task_type == "medium":
            # Дневной период для средних задач
            midday_start = wake_up_dt + timedelta(hours=4)
            midday_end = wake_up_dt + timedelta(hours=7)

            periods.append({
                "name": "Дневной период фокуса",
                "description": "Хорошее время для аналитических задач",
                "start": midday_start,
                "end": midday_end,
                "priority": "good",
                "reason": "Стабильная продуктивность через 4-7 часов после пробуждения"
            })

        else:  # light tasks
            # Гибкие периоды для легких задач
            flexible_start = wake_up_dt + timedelta(hours=1)
            flexible_end = bed_dt - timedelta(hours=2)

            periods.append({
                "name": "Гибкое рабочее время",
                "description": "Подходит для рутинных задач",
                "start": flexible_start,
                "end": flexible_end,
                "priority": "acceptable",
                "reason": "Любое время кроме вечернего спада (за 2 часа до сна)"
            })

        return periods

    except ValueError:
        return []


def parse_free_slots(free_slots_data: List[Dict[str, str]]) -> List[TimeSlot]:
    """Парсит свободные слоты времени"""
    slots = []

    for slot_data in free_slots_data:
        try:
            started_at = datetime.strptime(slot_data["started_at"], "%Y-%m-%d %H:%M:%S")
            ended_at = datetime.strptime(slot_data["ended_at"], "%Y-%m-%d %H:%M:%S")
            slots.append(TimeSlot(started_at=started_at, ended_at=ended_at))
        except (ValueError, KeyError):
            continue

    return sorted(slots, key=lambda x: x.started_at)


def find_best_schedule(
    creation_date: datetime,
    deadline_date: datetime,
    duration_minutes: int,
    free_slots: List[TimeSlot],
    productivity_periods: List[Dict[str, Any]],
    task_type: str,
    sleep_schedule: Dict[str, str]
) -> SchedulingResult:
    """Находит лучшее время для задачи"""

    now = datetime.now()
    duration = timedelta(minutes=duration_minutes)

    # 1. Проверяем, успеваем ли вообще до дедлайна
    earliest_start = max(now + timedelta(minutes=30), creation_date)
    earliest_end = earliest_start + duration

    if earliest_end > deadline_date:
        return SchedulingResult(
            is_scheduled=False,
            message=f"Невозможно выполнить задачу до дедлайна {deadline_date.strftime('%d.%m.%Y %H:%M')}. Требуется {duration_minutes} минут, но осталось только {int((deadline_date - earliest_start).total_seconds() / 60)} минут.",
            quality="impossible",
            deadline_met=False
        )

    # 2. Ищем в периоде продуктивности + свободных окнах (оптимальный вариант)
    for period in productivity_periods:
        if period["priority"] in ["optimal", "good"]:
            period_start = period["start"]
            period_end = period["end"]

            # Проверяем свободные слоты в этом периоде
            for free_slot in free_slots:
                # Находим пересечение свободного слота и периода продуктивности
                overlap_start = max(free_slot.started_at, period_start)
                overlap_end = min(free_slot.ended_at, period_end)

                if overlap_start < overlap_end:
                    available_duration = overlap_end - overlap_start

                    if available_duration >= duration:
                        # Нашли подходящий слот
                        task_start = overlap_start
                        task_end = task_start + duration

                        # Проверяем дедлайн
                        if task_end <= deadline_date:
                            time_to_deadline = deadline_date - task_end

                            return SchedulingResult(
                                is_scheduled=True,
                                slot={
                                    "start": task_start,
                                    "end": task_end
                                },
                                message=f"Запланировано в {period['name'].lower()}. {period['reason']} Время выбрано с учетом вашего расписания сна (подъем в {sleep_schedule['wake_up_time']}, отбой в {sleep_schedule['bed_time']}).",
                                quality=period["priority"],
                                peak_period=period["name"],
                                deadline_met=True,
                                time_until_deadline=f"{time_to_deadline.days}д {time_to_deadline.seconds // 3600}ч"
                            )

    # 3. Ищем в любых свободных окнах (хороший вариант)
    for free_slot in free_slots:
        if free_slot.ended_at < now or free_slot.started_at > deadline_date:
            continue

        available_duration = free_slot.ended_at - free_slot.started_at
        if available_duration >= duration:
            task_start = free_slot.started_at
            task_end = task_start + duration

            if task_end <= deadline_date:
                time_to_deadline = deadline_date - task_end

                return SchedulingResult(
                    is_scheduled=True,
                    slot={
                        "start": task_start,
                        "end": task_end
                    },
                    message="Запланировано в указанном свободном окне. Время не совпадает с пиками продуктивности, но соответствует вашему расписанию.",
                    quality="acceptable",
                    deadline_met=True,
                    time_until_deadline=f"{time_to_deadline.days}д {time_to_deadline.seconds // 3600}ч"
                )

    # 4. Рассчитываем на основе периодов продуктивности (без свободных окон)
    for period in productivity_periods:
        if period["priority"] in ["optimal", "good"]:
            # Пробуем завтра в этот период
            tomorrow = now.date() + timedelta(days=1)
            period_start_time = period["start"].time()
            period_end_time = period["end"].time()

            period_start = datetime.combine(tomorrow, period_start_time)
            period_end = datetime.combine(tomorrow, period_end_time)

            if period_end <= deadline_date:
                task_start = period_start
                task_end = task_start + duration

                if task_end <= period_end:
                    time_to_deadline = deadline_date - task_end

                    return SchedulingResult(
                        is_scheduled=True,
                        slot={
                            "start": task_start,
                            "end": task_end
                        },
                        message=f"Запланировано на завтра в {period['name'].lower()}. {period['reason']} Рекомендуется для оптимальной продуктивности.",
                        quality=period["priority"],
                        peak_period=period["name"],
                        deadline_met=True,
                        time_until_deadline=f"{time_to_deadline.days}д {time_to_deadline.seconds // 3600}ч"
                    )

    # 5. Резервный вариант: как можно раньше
    task_start = earliest_start
    task_end = earliest_start + duration

    if task_end <= deadline_date:
        time_to_deadline = deadline_date - task_end

        warning = ""
        if task_type == "deep" and task_start.hour >= 18:
            warning = " Внимание: сложная задача запланирована на вечер, что может снизить эффективность."

        return SchedulingResult(
            is_scheduled=True,
            slot={
                "start": task_start,
                "end": task_end
            },
            message=f"Запланировано на ближайшее доступное время.{warning} Это резервный вариант, так как не найдено совпадений с вашими предпочтениями.",
            quality="poor",
            deadline_met=True,
            time_until_deadline=f"{time_to_deadline.days}д {time_to_deadline.seconds // 3600}ч"
        )

    # 6. Не нашли подходящего времени
    return SchedulingResult(
        is_scheduled=False,
        message=f"Не удалось найти подходящее время. Попробуйте увеличить дедлайн или освободить больше времени в расписании.",
        quality="impossible",
        deadline_met=False
    )


# ==========================
# USER INTERFACE
# ==========================

def get_sleep_schedule_input() -> Dict[str, str]:
    """Запрашивает расписание сна"""

    print("\n" + "=" * 60)
    print("РАСПИСАНИЕ СНА")
    print("=" * 60)

    wake_up = input("\n⏰ Во сколько вы просыпаетесь? (например, 07:30): ").strip()
    if not wake_up:
        wake_up = "07:30"
    else:
        try:
            datetime.strptime(wake_up, "%H:%M")
        except ValueError:
            print("⚠️  Неверный формат, используется 07:30")
            wake_up = "07:30"

    bed_time = input("🌙 Во сколько вы ложитесь спать? (например, 23:00): ").strip()
    if not bed_time:
        bed_time = "23:00"
    else:
        try:
            datetime.strptime(bed_time, "%H:%M")
        except ValueError:
            print("⚠️  Неверный формат, используется 23:00")
            bed_time = "23:00"

    return {"wake_up_time": wake_up, "bed_time": bed_time}


def get_free_slots_input() -> List[Dict[str, str]]:
    """Запрашивает свободные окна"""

    print("\n" + "-" * 60)
    print("СВОБОДНЫЕ ОКНА ВРЕМЕНИ")
    print("-" * 60)

    print("\n📋 Пример формата: 2024-01-12 14:00:00")

    add_slots = input("\n➕ Добавить свободные окна? (да/нет): ").strip().lower()

    free_slots = []

    if add_slots in ['да', 'yes', 'y', 'д']:
        print("\n📝 Вводите окна (оставьте пустым для завершения):")

        slot_num = 1
        while True:
            print(f"\n   Окно #{slot_num}:")
            start_str = input("   Начало (ГГГГ-ММ-ДД ЧЧ:ММ:СС): ").strip()

            if not start_str:
                break

            end_str = input("   Конец (ГГГГ-ММ-ДД ЧЧ:ММ:СС): ").strip()

            if not end_str:
                print("   ⚠️  Нужно указать время окончания")
                continue

            try:
                datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
                datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")

                free_slots.append({
                    "started_at": start_str,
                    "ended_at": end_str
                })
                slot_num += 1

            except ValueError:
                print("   ⚠️  Неверный формат")

    return free_slots


def get_task_input() -> tuple[TaskInput, datetime, datetime]:
    """Получает данные о задаче"""

    print("\n" + "=" * 60)
    print("ПЛАНИРОВЩИК ЗАДАЧ")
    print("=" * 60)

    # Основные данные
    title = input("\n🏷️  Название задачи: ").strip()
    while not title:
        print("   ❌ Название обязательно!")
        title = input("🏷️  Название задачи: ").strip()

    description = 'пропылесосить квартиру'
    while not description:
        print("   ❌ Описание обязательно!")
        description = input("📄 Описание задачи: ").strip()

    # Дополнительные данные
    tags_input = input("\n🏷️  Теги (через запятую, Enter чтобы пропустить): ").strip()
    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()] if tags_input else None

    user_estimate = input("\n⭐ Оценка сложности (легко/средне/сложно, Enter чтобы пропустить): ").strip()
    user_estimate = user_estimate if user_estimate else None

    # Расписание и окна
    sleep_schedule = get_sleep_schedule_input()
    free_time_slots = get_free_slots_input()

    # Дедлайн
    print("\n" + "-" * 60)
    print("⏰ ДЕДЛАЙН")
    print("-" * 60)

    deadline_str = input("\n📅 Дедлайн (ДД.ММ.ГГГГ ЧЧ:ММ, Enter для авто-расчета): ").strip()

    creation_date = datetime.now()

    if deadline_str:
        try:
            deadline_date = datetime.strptime(deadline_str, "%d.%m.%Y %H:%M")
        except ValueError:
            print("⚠️  Неверный формат, ставим дедлайн через 3 дня")
            deadline_date = creation_date + timedelta(days=3)
            deadline_str = deadline_date.strftime("%d.%m.%Y %H:%M")
    else:
        deadline_date = creation_date.replace(hour=18, minute=0) + timedelta(days=3)
        deadline_str = deadline_date.strftime("%d.%m.%Y %H:%M")
        print(f"   ✅ Авто-дедлайн: {deadline_str}")

    # Создаем объект задачи
    task = TaskInput(
        title=title,
        description=description,
        tags=tags,
        user_estimate=user_estimate,
        deadline=deadline_str,
        free_time_slots=free_time_slots if free_time_slots else None,
        sleep_schedule=sleep_schedule
    )

    return task, creation_date, deadline_date


def format_datetime_for_display(dt: datetime) -> str:
    """Форматирует datetime для отображения"""
    return dt.strftime("%d.%m.%Y %H:%M")


def display_results(
    cognitive_result: CognitiveAnalysisResult,
    scheduling_result: SchedulingResult,
    task: TaskInput,
    creation_date: datetime,
    deadline_date: datetime
) -> None:
    """Отображает результаты анализа"""

    print(f"\n{'=' * 60}")
    print("🎯 РЕЗУЛЬТАТЫ АНАЛИЗА")
    print(f"{'=' * 60}")

    # Когнитивный анализ
    print(f"\n🧠 КОГНИТИВНЫЙ АНАЛИЗ:")
    print(f"   • Уровень концентрации: {cognitive_result.concentration_level}")
    print(f"   • Уверенность: {cognitive_result.confidence:.0%}")
    print(f"   • Рекомендуемое время: {cognitive_result.recommended_block_minutes} мин")
    print(f"   • Требуемая энергия: {cognitive_result.preferred_energy}")
    print(f"   • Обоснование: {cognitive_result.reason}")

    # Рекомендуемые действия
    if cognitive_result.actions:
        print(f"\n📋 РЕКОМЕНДУЕМЫЕ ДЕЙСТВИЯ:")
        for i, action in enumerate(cognitive_result.actions, 1):
            print(f"   {i}. {action}")

    # Планирование времени
    print(f"\n📅 ПЛАНИРОВАНИЕ ВРЕМЕНИ:")

    if scheduling_result.is_scheduled:
        slot = scheduling_result.slot
        if slot:
            print(f"   ✅ Задача запланирована")
            print(f"   • Начало: {format_datetime_for_display(slot['start'])}")
            print(f"   • Окончание: {format_datetime_for_display(slot['end'])}")
            print(f"   • Качество: {scheduling_result.quality}")

            if scheduling_result.peak_period:
                print(f"   • Период продуктивности: {scheduling_result.peak_period}")

            if scheduling_result.time_until_deadline:
                print(f"   • До дедлайна останется: {scheduling_result.time_until_deadline}")

        print(f"\n   💡 {scheduling_result.message}")
    else:
        print(f"   ❌ Задача не запланирована")
        print(f"   💡 {scheduling_result.message}")

    # JSON результат для фронтенда
    print(f"\n{'=' * 60}")
    print("📊 JSON-РЕЗУЛЬТАТ ДЛЯ ФРОНТЕНДА")
    print(f"{'=' * 60}")

    result_dict = {
        "cognitive_analysis": cognitive_result.model_dump(),
        "scheduling": {
            "is_scheduled": scheduling_result.is_scheduled,
            "slot": {
                "start": scheduling_result.slot["start"].isoformat() if scheduling_result.slot else None,
                "end": scheduling_result.slot["end"].isoformat() if scheduling_result.slot else None
            } if scheduling_result.slot else None,
            "message": scheduling_result.message,
            "quality": scheduling_result.quality,
            "peak_period": scheduling_result.peak_period,
            "deadline_met": scheduling_result.deadline_met,
            "time_until_deadline": scheduling_result.time_until_deadline
        },
        "task_info": {
            "title": task.title,
            "description": task.description,
            "tags": task.tags,
            "user_estimate": task.user_estimate,
            "deadline": task.deadline,
            "sleep_schedule": task.sleep_schedule,
            "creation_date": creation_date.isoformat(),
            "deadline_date": deadline_date.isoformat()
        }
    }

    print(json.dumps(result_dict, indent=2, ensure_ascii=False))

    # Также показываем удобный для чтения формат
    print(f"\n{'=' * 60}")
    print("👁️  ЧЕЛОВЕКО-ЧИТАЕМЫЙ ФОРМАТ")
    print(f"{'=' * 60}")

    if scheduling_result.is_scheduled and scheduling_result.slot:
        slot = scheduling_result.slot
        print(f"\n📅 РАСПИСАНИЕ:")
        print(f"   is_scheduled: {scheduling_result.is_scheduled}")
        print(f"   slot:")
        print(f"     start: {slot['start'].strftime('%Y-%m-%dT%H:%M:%S')}")
        print(f"     end: {slot['end'].strftime('%Y-%m-%dT%H:%M:%S')}")
        print(f"   message: \"{scheduling_result.message}\"")
        print(f"   quality: {scheduling_result.quality}")

        if scheduling_result.peak_period:
            print(f"   peak_period: \"{scheduling_result.peak_period}\"")

        print(f"   deadline_met: {scheduling_result.deadline_met}")

        if scheduling_result.time_until_deadline:
            print(f"   time_until_deadline: \"{scheduling_result.time_until_deadline}\"")


# ==========================
# MAIN EXECUTION
# ==========================

if __name__ == "__main__":
    try:
        print("\n" + "✨" * 30)
        print("ИНТЕЛЛЕКТУАЛЬНЫЙ ПЛАНИРОВЩИК ЗАДАЧ")
        print("✨" * 30)

        # 1. Получаем данные
        task, creation_date, deadline_date = get_task_input()

        # 2. Анализируем задачу
        print("\n" + "⏳" * 20)
        print("АНАЛИЗИРУЮ ЗАДАЧУ...")
        print("⏳" * 20)

        cognitive_result = analyze_task(task)

        # 3. Рассчитываем периоды продуктивности
        productivity_periods = []
        if task.sleep_schedule:
            productivity_periods = calculate_productivity_periods(
                task.sleep_schedule["wake_up_time"],
                task.sleep_schedule["bed_time"],
                cognitive_result.concentration_level
            )

        # 4. Парсим свободные слоты
        free_slots = parse_free_slots(task.free_time_slots) if task.free_time_slots else []

        # 5. Находим лучшее расписание
        scheduling_result = find_best_schedule(
            creation_date=creation_date,
            deadline_date=deadline_date,
            duration_minutes=cognitive_result.recommended_block_minutes,
            free_slots=free_slots,
            productivity_periods=productivity_periods,
            task_type=cognitive_result.concentration_level,
            sleep_schedule=task.sleep_schedule or {"wake_up_time": "07:30", "bed_time": "23:00"}
        )

        # 6. Показываем результаты
        display_results(
            cognitive_result=cognitive_result,
            scheduling_result=scheduling_result,
            task=task,
            creation_date=creation_date,
            deadline_date=deadline_date
        )

        print("\n" + "✅" * 20)
        print("АНАЛИЗ ЗАВЕРШЕН!")
        print("✅" * 20)

    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
    except Exception as e:
        print(f"\n\n❌ Ошибка: {e}")