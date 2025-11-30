class AddItem {
    AddItem({
        canAdd=false,
        urlToAdd=''
    }) {
        this.canAdd = canAdd;
        this.AddItem = urlToAdd
    }
}

/**
 * @param {Object} params
 * @param {null | string} [params.selector]
 * @param {string[]} [params.selectors]
 * @param {Map{}} [params.items]
 * @param {null | AddItem} [params.addItem]
 * @param {string} [params.title]
 * @returns {boolean | void}
 */
function initGlassSelect({
    selector=null,
    selectors=[],
    addItem=null,
    items=[],
    title='',
}) {
    if (selector) {
        let select = document.querySelector(selector);
        if (select === undefined) {
            console.error('Не получается инициалиизировать список!\nБлок не найден');
            return;
        }
        else{
            return initInterface({select: select, title: title, items: items});
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
}) {
    let main_select_block = createDiv({
        classList: ['glass_select'],
        id: select.id,
        onclick: () => {},
    });
    main_select_block.values = [];
    let drop_list = createDiv({
        classList: ['glass-select-drop-list'],
        onclick: () => {}, 
    });
    let selected_items = createDiv({
        classList: ['glass-select-selected-items'],
        onclick: () => {}, 
    });
    let selecet_title = createTextH({
        title: title,
        classList: ['glass-select-title'],
    });

    // -----------------------
    let dropListItemsBlock = createDiv({
        classList: ['glass-select-drop-selected-items'],    
    });
    let textInput = createInput({
        type: 'text',
        classList: ['glass-input-text', 'small-border', 'max-width'],
        placeholder:  'Введите текст...',
        onfocus: (event) => {            dropListItemsBlock.classList.add('drop-list-items-show');
            console.log('Сфокусировлись');
        },
        onfocusout: (event) => {
            dropListItemsBlock.classList.remove('drop-list-items-show');
            console.log('Расфокусировлись');
        },
    });

    for (let i = 0; i < items.length; i++) {
        let selectItem = createDiv({
            classList: ['glass-select-drop-list-value'],
            onclick: () => {
                dropListItemsBlock.classList.remove('drop-list-items-show');

                if (main_select_block.values.indexOf(items[i].id) == -1) {
                    main_select_block.values.push(items[i].id);
                    selected_items.appendChild(createSelectedItem({
                        value: items[i].id,
                        title: items[i].name,
                        main_select_block: main_select_block,
                    }));
                }
            }
        });
        let selectTitle = createTextH({
            title: items[i].name,
            hType: 'h6',
        });
        selectItem.appendChild(selectTitle);
        dropListItemsBlock.appendChild(selectItem);

        if (i != (items.length - 1)) {
                    dropListItemsBlock.appendChild(
                        document.createElement('hr')
                    );
                }
    }

    drop_list.appendChild(textInput);
    drop_list.appendChild(dropListItemsBlock);

    main_select_block.appendChild(selecet_title);
    main_select_block.appendChild(drop_list);
    main_select_block.appendChild(selected_items);

    console.log('main_select_block', main_select_block);
    select.style.display = 'none';
    select.insertAdjacentElement('afterEnd', main_select_block);

    return main_select_block;
}

function createSelectedItem({value, title, main_select_block}) {
    let selectedItem = createDiv({
        classList: ['glass-select-selected-item', 'glass-block'],
    });
    let SelectedTitle = createTextH({title: title, hType: 'h6'});
    let closeImg = document.createElement('img');
    closeImg.src = '../static/first_app/images/close.svg';
    let closeBtn = document.createElement('button');
    closeBtn.className = 'tag-close';
    closeBtn.type = 'button';
    closeBtn.ariaLabel = 'Удалить тэг';
    closeBtn.onclick = (event) => {
        main_select_block.values.splice(
            main_select_block.values.indexOf(value), 1
        );
        event.target.closest('.glass-select-selected-item').remove();
    };

    closeBtn.appendChild(closeImg);
    selectedItem.appendChild(SelectedTitle);
    selectedItem.appendChild(closeBtn);
    
    return selectedItem;
}


function createDiv({
    name='',
    classList=[],
    id='',
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
    hType='h1',
    name='',
    classList=[],
    id='',
}) {
    let newTextElement = document.createElement(hType);
    newTextElement.name = name;
    newTextElement.id = id;
    newTextElement.classList.add(...classList);
    newTextElement.innerText = title;

    return newTextElement;
}

function createInput({
    type='text',
    value=null,
    placeholder='',
    name='',
    classList=[],
    id='',
    onnclick=null,
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
    newInputElement.onclick = onnclick;
    newInputElement.onfocus = onfocus;
    newInputElement.onfocusout = onfocusout;

    return newInputElement
}

// ------------------------
//drop-list-items-show