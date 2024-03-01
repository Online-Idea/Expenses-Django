
document.addEventListener('DOMContentLoaded', () => {
    // Состояние приложения
    const state = {
        tableCreated: false,    // Флаг создания таблицы
        sortApplied: false,     // Флаг применения сортировки
        container: document.querySelector('#sort-fields-container'),   // Контейнер для сортировочных полей
        fieldSelect: document.querySelector('#id_fields'),             // Выпадающий список для выбора поля
        submitButton: document.querySelector('#apply-sort'),           // Кнопка применения сортировки
        resetSortLabel: document.querySelector('#reset-sort-label'),   // Крестик сброса сортировки
        toggleButton: document.querySelector('#toggle-sort'),          // Кнопка переключения видимости сортировочной формы
        searchButton: document.querySelector('#apply-search'),         // Кнопка применения поиска по VIn
        resetSearchLabel: document.querySelector('#reset-search-label'),    // Кнопка сброса поиска по Vin
        sortForm: document.querySelector('#sort-form'),                // Форма для сортировки
        sortLabel: document.querySelector('#sort-label'),              // Метка с информацией о примененной сортировке
        csrfToken: document.querySelector('input[name="csrfmiddlewaretoken"]').value,  // CSRF-токен
        vinSearchInput: document.querySelector('#id_vin_search'),
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
        ['№', 'Поле', 'Порядок', 'Удалить'].forEach(headerText => {
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
                const img = document.createElement('img');
                img.src = '/static/img/icon-garbage.svg';
                img.style.width = '24px';
                img.style.height = '24px';
                img.className = 'remove-button'
                td.appendChild(img);
                const sortField = {
                    field: fieldValue,
                    orderSelect: td.querySelector('select'),
                    removeButton: img,
                    tr: tr,
                };
                state.sortFields.push(sortField);
                img.addEventListener('click', () => removeSortField(sortField, tr));
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
        }
        updateRowNumbers();
    }

    /**
     * Переключает видимость сортировочной формы
     */
    function toggleSortForm() {
        state.sortForm.classList.toggle('d-none');
        state.toggleButton.textContent = state.sortForm.classList.contains('d-none') ? 'Сортировка ▶' : 'Сортировка ▼';
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
        state.resetSortLabel.classList.add('d-none');
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

    function resetTemplate() {
        const formData = new FormData();
        formData.append('reset', 'true');
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
                    const tbody = state.container.querySelector('tbody');
                    state.resetSearchLabel.classList.add('d-none');
                    state.vinSearchInput.value = ''
                    if (tbody) {
                        resetSort();
                        toggleSortForm();
                    }
                } else {
                    console.error('Ошибка при получении данных с сервера');
                }
            })
            .catch(error => {
                console.error('Ошибка при отправке данных:', error);
            });
    }

    // Инициализация состояния
    state.sortLabel.classList.add('hide');
    state.resetSortLabel.classList.add('d-none');
    state.submitButton.classList.add('d-none');
    state.resetSearchLabel.classList.add('d-none');
    state.sortLabel.textContent = 'Применена';

    // Обработчики событий

    state.toggleButton.addEventListener('click', toggleSortForm);
    state.resetSortLabel.addEventListener('click', resetTemplate);
    state.resetSearchLabel.addEventListener('click', resetTemplate);

    state.fieldSelect.addEventListener('change', () => {
        const selectedField = state.fieldSelect.options[state.fieldSelect.selectedIndex];
        if (selectedField) {
            const {value, text} = selectedField;
            addSortField(value, text);
        }
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
                    state.resetSortLabel.classList.remove('d-none');
                } else {
                    console.error('Ошибка при получении данных с сервера');
                }
            })
            .catch(error => {
                console.error('Ошибка при отправке данных:', error);
            });
    });

    state.searchButton.addEventListener('click', () => {
        const vinValue = state.vinSearchInput.value.trim();

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
                        state.resetSearchLabel.classList.remove('d-none');
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
