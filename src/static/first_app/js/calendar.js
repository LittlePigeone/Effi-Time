const TASKS_MOCK = [
    {
        id: 1,
        title: "Task 1",
        started_at: "16.11.2025 02:00",
        ended_at: "16.11.2025 12:00",
    },
    {
        id: 2,
        title: "Task 2",
        started_at: "16.11.2025 12:00",
        ended_at: "16.11.2025 20:00",
    },
    {
        id: 3,
        title: "Тут будет задача с навзвание подлинее",
        started_at: "15.11.2025 06:00",
        ended_at: "15.11.2025 10:00",
    },
    {
        id: 4,
        title: "Task 4",
        started_at: "15.11.2025 01:00",
        ended_at: "15.11.2025 05:00",
    },
    {
        id: 5,
        title: "Задача с очень длинным названием",
        started_at: "15.11.2025 12:00",
        ended_at: "15.11.2025 16:00",
    },
]

let dragTask = null;      // оригинальный блок
let ghost = null;         // призрак
let shadow = null;        // серая тень
let shiftX = 0;
let shiftY = 0;
let taskHeight = 0;
const TASK_OFFSET_MINUTES = 0;

function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}

function placeShadow(dayColumn, clientY) {
    if (!shadow) return;

    const colRect = dayColumn.getBoundingClientRect();
    let desiredTop = clientY - colRect.top - taskHeight / 2;
    let top = desiredTop;

    const colHeight = colRect.height;
    top = clamp(top, 0, Math.max(0, colHeight - taskHeight));

    const tasks = Array.from(dayColumn.querySelectorAll('.cal-task-block'))
        .filter(t => !t.classList.contains('cal-task-hidden'));

    const margin = 2; // как в cal-task-block

    let changed = true;
    let iter = 0;
    const maxIter = 20; // защита от бесконечных циклов

    while (changed && iter < maxIter) {
        iter++;
        changed = false;

        const shadowTop = top;
        const shadowBottom = shadowTop + taskHeight;

        for (const task of tasks) {
            const r = task.getBoundingClientRect();
            const taskTop = r.top - colRect.top;
            const taskBottom = taskTop + r.height;

            const overlap = shadowTop < taskBottom && shadowBottom > taskTop;
            if (overlap) {
                const taskCenter = (taskTop + taskBottom) / 2;
                const shadowCenter = (shadowTop + shadowBottom) / 2;

                if (shadowCenter < taskCenter) {
                    // вверх
                    top = taskTop - taskHeight - margin;
                } else {
                    // вниз
                    top = taskBottom + margin;
                }

                top = clamp(top, 0, Math.max(0, colHeight - taskHeight));
                changed = true;
                break;
            }
        }
    }

    // если дошли до лимита — просто прячем тень, чтобы не висло
    if (iter >= maxIter) {
        shadow.style.display = 'none';
        return;
    }

    shadow.style.top = top + 'px';
    shadow.style.display = 'flex';

    if (window.CALENDAR_PX_PER_MINUTE) {
        var minutesTotal = Math.round(top / window.CALENDAR_PX_PER_MINUTE);
        var hh = Math.floor(minutesTotal / 60);
        var mm = minutesTotal % 60;

        var hhStr = String(hh).padStart(2, '0');
        var mmStr = String(mm).padStart(2, '0');
        shadow.innerText = hhStr + ':' + mmStr;
    }

    shadow.style.display = 'flex';
}

function onMouseMove(e) {
    if (!ghost || !dragTask) return;

    // двигаем призрак
    ghost.style.left = (e.clientX - shiftX) + 'px';
    ghost.style.top  = (e.clientY - shiftY) + 'px';

    // временно прячем призрак для elementFromPoint
    ghost.style.pointerEvents = 'none';
    const elem = document.elementFromPoint(e.clientX, e.clientY);
    ghost.style.pointerEvents = '';

    if (!elem) return;

    const dayColumn = elem.closest('.day-column');
    if (!dayColumn) {
        if (shadow) shadow.style.display = 'none';
        return;
    }

    if (!shadow) return;

    // если тень в другой колонке — перенесём
    if (shadow.parentElement !== dayColumn) {
        dayColumn.appendChild(shadow);
    }

    placeShadow(dayColumn, e.clientY);
}

function onMouseUp(e) {
    if (!dragTask) return;

    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);

    if (shadow && shadow.parentElement) {
        const col = shadow.parentElement;
        dragTask.style.top = shadow.style.top;
        dragTask.style.left = '0px';
        dragTask.style.width = 'calc(100% - 4px)';
        dragTask.style.margin = '2px';
        col.appendChild(dragTask);
    }

    dragTask.classList.remove('cal-task-hidden');

    if (ghost && ghost.parentElement) ghost.parentElement.removeChild(ghost);
    if (shadow && shadow.parentElement) shadow.parentElement.removeChild(shadow);

    dragTask = null;
    ghost = null;
    shadow = null;
}

function onMouseDown(e) {
    const task = e.target.closest('.cal-task-block');
    if (!task) return;
    if (e.button !== 0) return; // только ЛКМ

    e.preventDefault();

    dragTask = task;
    const rect = task.getBoundingClientRect();
    shiftX = e.clientX - rect.left;
    shiftY = e.clientY - rect.top;
    taskHeight = rect.height;

    // скрываем оригинал
    dragTask.classList.add('cal-task-hidden');

    // создаём призрак
    ghost = dragTask.cloneNode(true);
    ghost.classList.add('cal-task-ghost');
    ghost.style.position = 'fixed';
    ghost.style.left = rect.left + 'px';
    ghost.style.top = rect.top + 'px';
    ghost.style.width = rect.width + 'px';
    ghost.style.height = rect.height + 'px';
    ghost.style.margin = '0';
    document.body.appendChild(ghost);

    // создаём тень
    shadow = document.createElement('div');
    shadow.className = 'cal-task-shadow glass-block';
    shadow.style.position = 'absolute';
    shadow.style.left = '0px';
    shadow.style.width = 'calc(100% - 4px)';
    shadow.style.height = rect.height + 'px';
    shadow.style.margin = '2px';

    const col = dragTask.closest('.day-column');
    if (col) {
        col.appendChild(shadow);
        const colRect = col.getBoundingClientRect();
        const initialTop = rect.top - colRect.top;
        shadow.style.top = initialTop + 'px';
    }

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
}

// ---------------------------------

// парсим "16.11.2025 10:00" -> { dateKey: "16.11.2025", minutesFromMidnight: 600 }
function parseDateTime(str) {
    var parts = str.split(' ');
    var datePart = parts[0];       // "16.11.2025"
    var timePart = parts[1];       // "10:00"

    var timePieces = timePart.split(':');
    var hh = parseInt(timePieces[0], 10);
    var mm = parseInt(timePieces[1], 10);

    return {
        dateKey: datePart,
        minutesFromMidnight: hh * 60 + mm,
    };
}

// основная функция рендера задач
function renderTasksOnCalendar(tasks) {
    // 1) узнаём высоту одного часового ряда
    var firstRow = document.querySelector('.calendar--row');
    if (!firstRow) return;

    var rowHeight = firstRow.getBoundingClientRect().height; // px за 1 час
    var pxPerMinute = rowHeight / 60.0;

    window.CALENDAR_PX_PER_MINUTE = pxPerMinute;

    // 2) очищаем календарь от старых задач
    document.querySelectorAll('.day-column').forEach(function(col) {
        // удаляем только задачи, не тени/призраки
        Array.from(col.querySelectorAll('.cal-task-block')).forEach(function(taskEl) {
            taskEl.remove();
        });
    });

    // 3) рисуем новые задачи
    tasks.forEach(function(task) {
        var startInfo = parseDateTime(task.started_at);
        var endInfo   = parseDateTime(task.ended_at);

        // пока считаем, что задача не переходит через сутки
        if (startInfo.dateKey !== endInfo.dateKey) {
            // если нужно поддержать задачи на 2 дня — придётся разбивать.
            return;
        }

        var dayColumn = document.querySelector(
            '.day-column[data-date="' + startInfo.dateKey + '"]'
        );
        if (!dayColumn) {
            // нет такой даты в текущей неделе — пропускаем
            return;
        }

        var durationMinutes = Math.max(15, endInfo.minutesFromMidnight - startInfo.minutesFromMidnight);
        var topPx = startInfo.minutesFromMidnight * pxPerMinute;
        var heightPx = durationMinutes * pxPerMinute;

        // создаём DOM-элемент задачи
        var el = document.createElement('div');
        el.className = 'cal-task-block glass-block small-border';
        el.dataset.id = task.id;

        el.style.top = topPx + 'px';
        el.style.height = heightPx + 'px';

        // простое содержание: заголовок + время
        el.innerHTML = `
            <div class="cal-task-info">
                <hr class="cal-task-status">
                <div class="cal-task-name-n-time">
                    <div class="cal-task-name">${task.title}</div>
                    <div class="cal-task-time">${task.started_at.split(' ')[1]} – ${task.ended_at.split(' ')[1]}</div>                                            
                </div>
            </div>
        `;

        dayColumn.appendChild(el);
    });
}

// ---------------------------------

document.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('mousedown', onMouseDown);

    renderTasksOnCalendar(TASKS_MOCK);


});