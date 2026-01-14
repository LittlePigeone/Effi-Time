class AddItem {
    AddItem({
        canAdd=false,
        urlToAdd=''
    }) {
        this.canAdd = canAdd;
        this.urlToAdd = urlToAdd;
    }
}

/**
 * @param {Object} params
 * @param {null | string} [params.selector]
 * @param {string[]} [params.selectors]
 * @param {Map[]} [params.items]
 * @param {null | AddItem} [params.addItem]
 * @param {string} [params.title]
 * @param {boolean} [params.multiple]
 * @param {int | string | null} [params.value]
 * @param {Array<int | string> | null} [params.values]
 * @returns {boolean | void}
 */
function initGlassSelect({
    selector=null,
    selectors=[],
    items=[],
    addItem=null,
    title="",
    multiple=false,
    value=null,
    values=null,
}) {
    if (selector) {
        let select = document.querySelector(selector);
        if (select === undefined) {
            console.error('Не получается инициалиизировать список!\nБлок не найден');
            return;
        }
        else {
            return initInterface({
                select: select,
                title: title,
                items: items,
                multiple: multiple,
                value: value,
                values: values,
            });
        }
    }
    else if (selectors.length > 1) {
        let selects = [];
        selectors.forEach((selector, i) => {
            let item = document.querySelector(selector);
            if (item) {
                selects.push(item);
            }
        });
        if (selects.length != selectors.length) {
            console.error('Не получается инициалиизировать список!\nКакой-то из блоков не найден');
            return;
        }
    }
    else {
        return;
    }
}

function initInterface({
    select,
    title,
    items,
    multiple=false,
    value=null,
    values=null,
}) {
    let main_select_block = createDiv({
        classList: ["glass-select"],
        id: select.id,
        onclick: (event) => {
            // Останавливаем всплытие события, чтобы не сработал глобальный обработчик
            event.stopPropagation();
        },
    });

    // Инициализация values в зависимости от режима
    if (multiple) {
        main_select_block.values = [];
    } else {
        main_select_block.values = null;
    }
    main_select_block.multiple = multiple;

    let drop_list = createDiv({
        classList: ["glass-select--drop-list"],
        onclick: (event) => {
            event.stopPropagation();
        },
    });
    let selected_items = createDiv({
        classList: ["glass-select--selected-items"],
        onclick: (event) => {
            event.stopPropagation();
        },
    });
    let select_title = createTextH({
        title: title,
        classList: ["glass-select--title"],
    });
    // ----------
    let dropListItemsBlock = createDiv({
        classList: ["glass-select--drop-list--items"],
    });
    let textInput = createInput({
        type: "text",
        classList: ["glass-input-text", "small-border", "max-width"],
        placeholder: "Введите текст...",
        onfocus: (event) => {
            // Закрываем все другие открытые селекты
            closeAllGlassSelects();

            dropListItemsBlock.classList.add('drop-list--items--show');
            console.log('Сфокусировались');
        },
        onclick: (event) => {
            event.stopPropagation();
        },
    });

    for (let i = 0; i < items.length; i++) {
        let selectItem = createDiv({
            classList: ['glass-select--drop-list--value'],
            onclick: (event) => {
                event.stopPropagation();

                if (multiple) {
                    // Режим multiple: работаем со списком
                    if (main_select_block.values.indexOf(items[i].id) == -1) {
                        main_select_block.values.push(items[i].id);
                        selected_items.appendChild(createSelectedItem({
                            value: items[i].id,
                            title: items[i].name,
                            main_select_block: main_select_block,
                            multiple: multiple,
                        }));
                        // Добавляем класс selected к элементу списка
                        selectItem.classList.add('selected');
                    }
                    // В режиме multiple не закрываем список после выбора
                } else {
                    // Режим single: заменяем значение

                    // Убираем подсветку со всех элементов
                    dropListItemsBlock.querySelectorAll('.glass-select--drop-list--value').forEach(item => {
                        item.classList.remove('selected');
                    });

                    main_select_block.values = items[i].id;

                    // Очищаем все предыдущие выбранные элементы
                    selected_items.innerHTML = '';

                    // Добавляем новый выбранный элемент
                    selected_items.appendChild(createSelectedItem({
                        value: items[i].id,
                        title: items[i].name,
                        main_select_block: main_select_block,
                        multiple: multiple,
                    }));

                    // Добавляем класс selected к текущему элементу
                    selectItem.classList.add('selected');

                    // В режиме single закрываем список после выбора
                    dropListItemsBlock.classList.remove('drop-list--items--show');
                }
            }
        });

        // Сохраняем ссылку на элемент для возможности управления подсветкой
        selectItem.dataset.itemId = items[i].id;

        let selectItemTitle = createTextH({
            title: items[i].name,
            hType: "h6",
        });
        selectItem.appendChild(selectItemTitle);
        dropListItemsBlock.appendChild(selectItem);

        if (i != (items.length - 1)) {
            dropListItemsBlock.appendChild(
                document.createElement('hr')
            );
        }
    }


    drop_list.appendChild(textInput);
    drop_list.appendChild(dropListItemsBlock);

    main_select_block.appendChild(select_title);
    main_select_block.appendChild(drop_list);
    main_select_block.appendChild(selected_items);


    select.style.display = 'none';
    select.insertAdjacentElement('afterEnd', main_select_block);

    // Инициализация предустановленных значений
    if (multiple && values && Array.isArray(values)) {
        // Multiple режим: устанавливаем массив значений
        values.forEach(val => {
            const item = items.find(i => i.id === val);
            if (item) {
                main_select_block.values.push(item.id);
                selected_items.appendChild(createSelectedItem({
                    value: item.id,
                    title: item.name,
                    main_select_block: main_select_block,
                    multiple: multiple,
                }));
                // Подсвечиваем элемент в списке
                const dropListItem = dropListItemsBlock.querySelector(`.glass-select--drop-list--value[data-item-id="${item.id}"]`);
                if (dropListItem) {
                    dropListItem.classList.add('selected');
                }
            }
        });
    } else if (!multiple && value !== null) {
        // Single режим: устанавливаем одно значение
        const item = items.find(i => i.id === value);
        if (item) {
            main_select_block.values = item.id;
            selected_items.appendChild(createSelectedItem({
                value: item.id,
                title: item.name,
                main_select_block: main_select_block,
                multiple: multiple,
            }));
            // Подсвечиваем элемент в списке
            const dropListItem = dropListItemsBlock.querySelector(`.glass-select--drop-list--value[data-item-id="${item.id}"]`);
            if (dropListItem) {
                dropListItem.classList.add('selected');
            }
        }
    }

    return main_select_block;
}

function createSelectedItem({value, title, main_select_block, multiple=false}) {
    let selectedItem = createDiv({
        classList: ["glass-select--selected-item", "glass-block"],
    });
    let selectedTitle = createTextH({title: title, hType: "h6"});
    let closeImg = document.createElement('img');
    closeImg.src = "../static/first_app/images/close.svg";
    let closeBtn = document.createElement('button');
    closeBtn.className = "tag-close";
    closeBtn.type = "button";
    closeBtn.ariaLabel = "Удалить тэг";
    closeBtn.onclick = (event) => {
        event.stopPropagation();

        if (multiple) {
            // Режим multiple: удаляем из массива
            main_select_block.values.splice(
                main_select_block.values.indexOf(value), 1
            );
        } else {
            // Режим single: обнуляем значение
            main_select_block.values = null;
        }

        // Убираем подсветку с соответствующего элемента в выпадающем списке
        const dropListItem = main_select_block.querySelector(`.glass-select--drop-list--value[data-item-id="${value}"]`);
        if (dropListItem) {
            dropListItem.classList.remove('selected');
        }

        event.target.closest('.glass-select--selected-item').remove();
    };

    closeBtn.appendChild(closeImg);
    selectedItem.appendChild(selectedTitle);
    selectedItem.appendChild(closeBtn);

    return selectedItem;
}

function createDiv({
    name="",
    classList=[],
    id="",
    onclick=null,
}) {
    let newDiv = document.createElement('div');
    newDiv.name = name;
    newDiv.classList.add(...classList);
    newDiv.id = id;
    newDiv.onclick = onclick;

    return newDiv;
}

function createTextH({
    title,
    hType="h1",
    name="",
    classList=[],
    id="",
}) {
    let newTextElement = document.createElement(hType);
    newTextElement.name = name;
    newTextElement.id = id;
    newTextElement.classList.add(...classList);
    newTextElement.innerText = title;

    return newTextElement;
}

function createInput({
    type="text",
    value=null,
    placeholder="",
    name="",
    classList=[],
    id="",
    onclick=null,
    onfocus=null,
    onfocusout=null,
}) {
    let newInputElement = document.createElement('input');
    newInputElement.type = type;
    newInputElement.value = value;
    newInputElement.placeholder = placeholder;
    newInputElement.name = name;
    newInputElement.classList.add(...classList);
    newInputElement.id = id;
    newInputElement.onclick = onclick;
    newInputElement.onfocus = onfocus;
    newInputElement.onfocusout = onfocusout;

    return newInputElement;
}
// -----------

// Глобальная функция для закрытия всех открытых селектов
function closeAllGlassSelects() {
    document.querySelectorAll('.glass-select--drop-list--items').forEach(item => {
        item.classList.remove('drop-list--items--show');
    });
}

// Глобальный обработчик кликов для закрытия селектов при клике вне их
document.addEventListener('click', (event) => {
    // Проверяем, что клик был не внутри glass-select
    if (!event.target.closest('.glass-select')) {
        closeAllGlassSelects();
    }
});

// drop-list--items--show