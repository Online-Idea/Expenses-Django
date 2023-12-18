/*----------------Список клиентов--------------------*/

class Accordion {
    constructor(el) {
        // Store the <details> element
        this.el = el;
        // Store the <summary> element
        this.summary = el.querySelector('summary');
        // Store the <div class="content"> element
        this.content = el.querySelector('.content');

        // Store the animation object (so we can cancel it if needed)
        this.animation = null;
        // Store if the element is closing
        this.isClosing = false;
        // Store if the element is expanding
        this.isExpanding = false;
        // Detect user clicks on the summary element
        this.summary.addEventListener('click', (e) => this.onClick(e));
    }

    onClick(e) {
        // Stop default behaviour from the browser
        e.preventDefault();
        // Add an overflow on the <details> to avoid content overflowing
        this.el.style.overflow = 'hidden';
        // Check if the element is being closed or is already closed
        if (this.isClosing || !this.el.open) {
            this.open();
            // Check if the element is being openned or is already open
        } else if (this.isExpanding || this.el.open) {
            this.shrink();
        }
    }

    shrink() {
        // Set the element as "being closed"
        this.isClosing = true;

        // Store the current height of the element
        const startHeight = `${this.el.offsetHeight}px`;
        // Calculate the height of the summary
        const endHeight = `${this.summary.offsetHeight}px`;

        // If there is already an animation running
        if (this.animation) {
            // Cancel the current animation
            this.animation.cancel();
        }

        // Start a WAAPI animation
        this.animation = this.el.animate({
            // Set the keyframes from the startHeight to endHeight
            height: [startHeight, endHeight]
        }, {
            duration: 400,
            easing: 'ease-out'
        });

        // When the animation is complete, call onAnimationFinish()
        this.animation.onfinish = () => this.onAnimationFinish(false);
        // If the animation is cancelled, isClosing variable is set to false
        this.animation.oncancel = () => this.isClosing = false;
    }

    open() {
        // Apply a fixed height on the element
        this.el.style.height = `${this.el.offsetHeight}px`;
        // Force the [open] attribute on the details element
        this.el.open = true;
        // Wait for the next frame to call the expand function
        window.requestAnimationFrame(() => this.expand());
    }

    expand() {
        // Set the element as "being expanding"
        this.isExpanding = true;
        // Get the current fixed height of the element
        const startHeight = `${this.el.offsetHeight}px`;
        // Calculate the open height of the element (summary height + content height)
        const endHeight = `${this.summary.offsetHeight + this.content.offsetHeight}px`;

        // If there is already an animation running
        if (this.animation) {
            // Cancel the current animation
            this.animation.cancel();
        }

        // Start a WAAPI animation
        this.animation = this.el.animate({
            // Set the keyframes from the startHeight to endHeight
            height: [startHeight, endHeight]
        }, {
            duration: 400,
            easing: 'ease-out'
        });
        // When the animation is complete, call onAnimationFinish()
        this.animation.onfinish = () => this.onAnimationFinish(true);
        // If the animation is cancelled, isExpanding variable is set to false
        this.animation.oncancel = () => this.isExpanding = false;
    }

    onAnimationFinish(open) {
        // Set the open attribute based on the parameter
        this.el.open = open;
        // Clear the stored animation
        this.animation = null;
        // Reset isClosing & isExpanding
        this.isClosing = false;
        this.isExpanding = false;
        // Remove the overflow hidden and the fixed height
        this.el.style.height = this.el.style.overflow = '';
    }
}

document.querySelectorAll('details').forEach((el) => {
    new Accordion(el);
});

// Чекбокс выбрать все чекбоксы
//function toggle(source, checkboxName) {
//    var checkboxes = document.querySelectorAll('input[name="' + checkboxName + '"]');
//    for (var i = 0; i < checkboxes.length; i++) {
//        if (checkboxes[i] != source)
//            checkboxes[i].checked = source.checked;
//    }
//}
// Отмечает те чекбоксы которые были ранее выбраны
function selected_checkboxes(elements, checkboxName, selectAllName) {
    var checkboxes = document.getElementsByName(checkboxName);
    if (elements.length != checkboxes.length) {
        for(var i = 0, n = checkboxes.length; i < n; i++) {
            if (elements.includes(checkboxes[i].value)) {
                checkboxes[i].checked = true;
            } else {
                checkboxes[i].checked = false;
            }
        }
        var selectAll = $('input[type=checkbox][name=' + selectAllName + ']').prop('checked', false);
    }
    //    var selectAll = checkboxes[0].parentElement.parentElement.parentElement.parentElement.querySelector('.selectAll');
    //    selectAll.checked = false;
}

/*---------------------------------------------------*/

document.addEventListener('DOMContentLoaded', () => {
    // Состояние приложения
    const state = {
        tableCreated: false,    // Флаг создания таблицы
        sortApplied: false,     // Флаг применения сортировки
        container: document.querySelector('#sort-fields-container'),  // Контейнер для сортировочных полей
        fieldSelect: document.querySelector('#id_fields'),             // Выпадающий список для выбора поля
        addButton: document.querySelector('#add-sort-field'),          // Кнопка добавления сортировочного поля
        submitButton: document.querySelector('#apply-sort'),           // Кнопка применения сортировки
        resetButton: document.querySelector('#reset-sort'),            // Кнопка сброса сортировки
        toggleButton: document.querySelector('#toggle-sort'),          // Кнопка переключения видимости сортировочной формы
        searchButton: document.querySelector('#apply-search'),
        sortForm: document.querySelector('#sort-form'),                // Форма для сортировки
        sortLabel: document.querySelector('#sort-label'),              // Метка с информацией о примененной сортировке
        csrfToken: document.querySelector('input[name="csrfmiddlewaretoken"]').value,  // CSRF-токен
        sortFields: [],         // Массив объектов с информацией о сортировочных полях
    };

    /**
     * Создает таблицу для отображения сортировочных полей
     */
    function createTable() {
        const table = document.createElement('table');
        table.className = 'table';
        const thead = document.createElement('thead');
        const trHead = document.createElement('tr');
        ['№', 'Категория', 'Порядок', 'Удалить'].forEach(headerText => {
            const th = document.createElement('th');
            th.scope = 'col';
            th.textContent = headerText;
            trHead.appendChild(th);
        });
        thead.appendChild(trHead);
        const tbody = document.createElement('tbody');
        table.appendChild(thead);
        table.appendChild(tbody);
        state.container.appendChild(table);
        state.tableCreated = true;
        state.submitButton.classList.remove('d-none');
    }

    /**
     * Добавляет сортировочное поле в таблицу
     * @param {string} fieldValue - Значение поля для сортировки
     * @param {string} fieldText - Текстовое описание поля для отображения в таблице
     */
    function addSortField(fieldValue, fieldText) {
        if (!state.tableCreated) {
            createTable();
        }
        if (!state.sortLabel.classList.contains('hide')) {
            state.resetButton.classList.remove('d-none');
        }
        const tbody = state.container.querySelector('tbody');
        const tr = document.createElement('tr');
        ['№', fieldText, 'Порядок', 'Удалить'].forEach((text, index) => {
            const td = document.createElement(index === 0 ? 'th' : 'td');
            if (index === 0) {
                td.scope = 'row';
                td.textContent = tbody.children.length + 1;
            } else if (index === 1) {
                td.textContent = fieldText;
            } else if (index === 2) {
                const orderSelect = document.createElement('select');
                orderSelect.name = `order_${state.sortFields.length}`;
                orderSelect.className = 'form-select';
                ['asc', 'desc'].forEach((value, index) => {
                    const option = document.createElement('option');
                    option.value = value;
                    option.text = index === 0 ? 'Возрастание' : 'Убывание';
                    orderSelect.appendChild(option);
                });
                td.appendChild(orderSelect);
                const sortField = {
                    field: fieldValue,
                    orderSelect: orderSelect,
                };
                state.sortFields.push(sortField);
                orderSelect.addEventListener('change', () => updateSortField(sortField, td));
                state.submitButton.classList.remove('d-none');
            } else if (index === 3) {
                const removeButton = document.createElement('button');
                removeButton.type = 'button';
                removeButton.textContent = '';
                removeButton.className = 'btn btn-danger';
                const img = document.createElement('img');
                img.src = '/static/img/remove_icon_.svg';
                img.style.width = '24px';
                img.style.height = '24px';
                removeButton.appendChild(img);
                td.appendChild(removeButton);
                const sortField = {
                    field: fieldValue,
                    orderSelect: td.querySelector('select'),
                    removeButton: removeButton,
                    tr: tr,
                };
                state.sortFields.push(sortField);
                removeButton.addEventListener('click', () => removeSortField(sortField, tr));
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    }

    /**
     * Обновляет значение сортировки для указанного поля
     * @param {Object} sortField - Объект с информацией о сортировочном поле
     * @param {HTMLElement} td - Ячейка таблицы, соответствующая сортировочному полю
     */
    function updateSortField(sortField, td) {
        const index = state.sortFields.findIndex(item => item.orderSelect === sortField.orderSelect);
        if (index !== -1) {
            state.sortFields[index].order = sortField.orderSelect.value;
        }
    }

    /**
     * Удаляет сортировочное поле из таблицы
     * @param {Object} sortField - Объект с информацией о сортировочном поле
     * @param {HTMLElement} tr - Строка таблицы, соответствующая сортировочному полю
     */
    function removeSortField(sortField, tr) {
        const tbody = state.container.querySelector('tbody');
        tbody.removeChild(tr);
        const index = state.sortFields.findIndex(item => item.orderSelect === sortField.orderSelect);
        if (index !== -1) {
            state.sortFields.splice(index, 1);
        }
        if (tbody.children.length === 0) {
            state.container.removeChild(state.container.firstChild);
            state.tableCreated = false;
            state.submitButton.classList.add('d-none');
            state.resetButton.classList.add('d-none');
        }
        state.resetButton.classList.add('d-none');
        updateRowNumbers();
    }

    /**
     * Переключает видимость сортировочной формы
     */
    function toggleSortForm() {
        state.sortForm.classList.toggle('d-none');
        state.toggleButton.textContent = state.sortForm.classList.contains('d-none') ? 'Показать сортировку ▶' : 'Скрыть сортировку ▼';
    }

    /**
     * Сбрасывает сортировку
     */
    function resetSort() {
        const tbody = state.container.querySelector('tbody');
        tbody.innerHTML = '';
        state.sortFields = [];
        state.container.removeChild(state.container.firstChild);
        state.tableCreated = false;
        state.submitButton.classList.add('d-none');
        state.resetButton.classList.add('d-none');
        state.sortLabel.classList.add('hide');
        state.sortApplied = false;
    }

    /**
     * Обновляет номера строк в таблице
     */
    function updateRowNumbers() {
        const tbody = state.container.querySelector('tbody');

        if (tbody) {
            const rows = tbody.querySelectorAll('tr');

            rows.forEach((row, index) => {
                const cells = row.querySelectorAll('th, td');
                cells[0].textContent = index + 1;
            });
        }
    }

    // Инициализация состояния
    state.sortLabel.classList.add('hide');
    state.resetButton.classList.add('d-none');
    state.submitButton.classList.add('d-none');
    state.sortLabel.textContent = 'Применена сортировка';

    // Обработчики событий
    state.addButton.addEventListener('click', () => {
        const selectedField = state.fieldSelect.options[state.fieldSelect.selectedIndex];
        if (selectedField) {
            const { value, text } = selectedField;
            addSortField(value, text);
        }
    });

    state.resetButton.addEventListener('click', () => {
        const formData = new FormData();
        formData.append('reset-sort', 'true');
        const endpointURL = '/ads/';

        fetch(endpointURL, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': state.csrfToken,
            },
            credentials: 'include',
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    resetSort();
                    const adsContainer = document.querySelector('#ads-container');
                    adsContainer.innerHTML = data.html;
                    toggleSortForm();
                } else {
                    console.error('Ошибка при получении данных с сервера');
                }
            })
            .catch(error => {
                console.error('Ошибка при отправке данных:', error);
            });
    });

    state.submitButton.addEventListener('click', () => {
        const formData = new FormData();
        formData.append('apply-sort', 'true');
        const endpointURL = '/ads/';
        state.sortLabel.classList.remove('hide');
        state.sortApplied = true;

        state.sortFields.forEach((sortField, index) => {
            formData.append(`field_${index}`, sortField.field);
            formData.append(`order_${index}`, sortField.order);
        });

        fetch(endpointURL, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': state.csrfToken,
            },
            credentials: 'include',
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const adsContainer = document.querySelector('#ads-container');
                    adsContainer.innerHTML = data.html;
                    toggleSortForm();
                    state.resetButton.classList.remove('d-none');
                } else {
                    console.error('Ошибка при получении данных с сервера');
                }
            })
            .catch(error => {
                console.error('Ошибка при отправке данных:', error);
            });
    });

    state.toggleButton.addEventListener('click', toggleSortForm);

    state.searchButton.addEventListener('click', () => {
        const vinSearchInput = document.querySelector('#id_vin_search');
        const vinValue = vinSearchInput.value.trim();

        if (vinValue !== '') {
            const formData = new FormData();
            formData.append('apply-search', 'true');
            formData.append('vin_search', vinValue);
            const endpointURL = '/ads/';


            fetch(endpointURL, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': state.csrfToken,
                },
                credentials: 'include',
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const adsContainer = document.querySelector('#ads-container');
                    adsContainer.innerHTML = data.html;
                    toggleSortForm();
                    state.resetButton.classList.remove('d-none');
                } else {
                    console.error('Ошибка при получении данных с сервера');
                }
            })
            .catch(error => {
                console.error('Ошибка при отправке данных:', error);
            });
        }
    });
});


