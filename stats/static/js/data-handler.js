document.addEventListener('DOMContentLoaded', () => {
    // Состояние приложения
    const state = {
        tableCreated: false,    // Флаг создания таблицы
        sortApplied: false,     // Флаг применения сортировки
        sortContainer: document.querySelector('#sort-fields-container'),   // Контейнер для сортировочных полей
        fieldSelect: document.querySelector('#id_fields'),             // Выпадающий список для выбора поля
        sortSubmitButton: document.querySelector('#apply-sort'),           // Кнопка применения сортировки
        sortResetButton: document.querySelector('#reset-sort-label'),   // Крестик сброса сортировки
        sortToggleButton: document.querySelector('#toggle-sort'),          // Кнопка переключения видимости сортировочной формы
        sortForm: document.querySelector('#sort-form'),  // Форма для сортировки

        toggleButtonFilter: document.querySelector('#toggle-filter'),
        searchButton: document.querySelector('#apply-search'),         // Кнопка применения поиска по VIn
        resetSearchLabel: document.querySelector('#reset-search-label'),    // Кнопка сброса поиска по Vin
        filterForm: document.querySelector('.filter-container'),
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
        table.className = 'table table-striped';  // Добавляем классы для стилей
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
        state.sortContainer.appendChild(table);
        state.tableCreated = true;
        state.sortSubmitButton.classList.remove('d-none');
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
        const tbody = state.sortContainer.querySelector('tbody');
        const tr = document.createElement('tr');

        const thIndex = document.createElement('th');
        thIndex.scope = 'row';
        thIndex.textContent = tbody.children.length + 1;
        tr.appendChild(thIndex);

        const tdField = document.createElement('td');
        tdField.textContent = fieldText;
        tr.appendChild(tdField);

        const tdOrder = document.createElement('td');
        const orderSelect = document.createElement('select');
        orderSelect.name = `order_${state.sortFields.length}`;
        orderSelect.className = 'form-select';
        ['asc', 'desc'].forEach((value, index) => {
            const option = document.createElement('option');
            option.value = value;
            option.text = index === 0 ? 'Возрастание' : 'Убывание';
            orderSelect.appendChild(option);
        });
        tdOrder.appendChild(orderSelect);
        tr.appendChild(tdOrder);

        const tdRemove = document.createElement('td');
        const img = document.createElement('img');
        img.src = '/static/img/icon-garbage.svg';
        img.style.width = '24px';
        img.style.cursor = 'pointer';
        img.className = 'remove-button';
        tdRemove.appendChild(img);
        tr.appendChild(tdRemove);

        const sortField = {
            field: fieldValue,
            orderSelect: orderSelect,
            order: orderSelect.value
        };

        state.sortFields.push(sortField);
        tbody.appendChild(tr);

        orderSelect.addEventListener('change', () => updateSortField(sortField));
        img.addEventListener('click', () => removeSortField(fieldValue, tr));

        state.sortSubmitButton.classList.remove('d-none');
    }

    /**
     * Обновляет значение сортировки для указанного поля
     * @param {Object} sortField - Объект с информацией о сортировочном поле
     * @param {HTMLElement} td - Ячейка таблицы, соответствующая сортировочному полю
     */
    function updateSortField(sortField) {
        const index = state.sortFields.findIndex(item => item.orderSelect === sortField.orderSelect);
        if (index !== -1) {
            state.sortFields[index].order = sortField.orderSelect.value;
        }
    }

    /**
     * Удаляет сортировочное поле из таблицы
     * @param {Object} nameField - Объект с информацией о сортировочном поле
     * @param {HTMLElement} tr - Строка таблицы, соответствующая сортировочному полю
     */
    function removeSortField(nameField, tr) {
        const index = state.sortFields.findIndex(item => item.field === nameField);
        if (index !== -1) {
            state.sortFields.splice(index, 1);
        }
        const tbody = state.sortContainer.querySelector('tbody');
        tbody.removeChild(tr);
        // Если удаляется последняя строка, удаляем всю таблицу
        if (tbody.children.length === 0) {
            resetSortUI();
            state.sortToggleButton.textContent = state.sortForm.classList.contains('d-none') ? 'Сортировка ▶' : 'Сортировка ▼';
            state.sortForm.classList.add('d-none');
            state.fieldSelect.classList.add('d-none');
        }
        updateRowNumbers();
    }

    /**
     * Переключает видимость сортировочной формы
     */
    function toggleSortForm() {
        state.fieldSelect.classList.toggle('d-none')
        state.sortForm.classList.toggle('d-none');
        state.sortToggleButton.textContent = state.sortForm.classList.contains('d-none') ? 'Сортировка ▶' : 'Сортировка ▼';
    }

    function toggleFilterForm() {
        state.filterForm.classList.toggle('d-none');
        state.toggleButtonFilter.textContent = state.filterForm.classList.contains('d-none') ? 'Фильтр ▶' : 'Фильтр ▼';
    }

    function resetSearchUI() {
        state.resetSearchLabel.classList.add('d-none');
        state.vinSearchInput.value = '';
    }

    /**
     * Сбрасывает сортировку, очищает таблицу и возвращает состояние сортировочного контейнера в исходное
     */
    function resetSortUI() {
        const sortTable = state.sortContainer.querySelector('table');
        if (sortTable) {
            state.sortContainer.removeChild(sortTable);
        }

        state.sortFields = [];
        state.tableCreated = false;
        state.sortSubmitButton.classList.add('d-none');
        state.sortResetButton.classList.add('d-none');
        state.sortLabel.classList.add('hide');
        state.sortApplied = false;
        state.sortForm.classList.add('d-none');
        state.fieldSelect.classList.add('d-none');
    }

    /**
     * Обновляет номера строк в таблице
     */
    function updateRowNumbers() {
        const tbody = state.sortContainer.querySelector('tbody');
        if (tbody) {
            const rows = tbody.querySelectorAll('tr');
            rows.forEach((row, index) => {
                const cells = row.querySelectorAll('th, td');
                cells[0].textContent = index + 1;
            });
        }
    }

    function collectData() {
        const data = {};
        data['sort'] = {};
        state.sortFields.forEach((sortField, index) => {
            data['sort'][`field_${index}`] = sortField.field;
            data['sort'][`order_${index}`] = sortField.order;
        });
        const vinValue = state.vinSearchInput.value.trim();
        data['search'] = {};
        data['search']['vin_search'] = vinValue;
        data['filters'] = filterTracker.getFilters()

        return data
    }


// Объект для отслеживания выбранных виджетов
    const handleTracker = {
        widgets: {},

        // Метод для добавления значений виджета
        addField(field, values) {
            if (field === 'sort') {
                this.widgets[field] = {};
                values.forEach((sortField, index) => {
                    this.widgets[field][`field_${index}`] = sortField.field;
                    this.widgets[field][`order_${index}`] = sortField.order;
                });
            } else if (field === 'search') {
                this.widgets[field] = {};
                // const vinValue = state.vinSearchInput.value.trim();
                this.widgets[field]['vin_search'] = values;
            } else if (field === 'filters') {
                this.widgets[field] = values
            }
        },

        // Метод для удаления значений виджета
        removeField(field) {
            if (field in this.widgets) {
                delete this.widgets[field]
            } else {
                console.error(`Виджет с полем ${field} не существует.`);
            }
        },
        // Метод для получения применённых виджетов
        getField(field) {
            return this.widgets[field];
        },

        // Метод для получения применённых виджетов
        getState() {
            return this.widgets;
        },
        // Метод для очистки всех выбранных виджетов
        clearState() {
            this.widgets = {}
        }
    };

    function resetTemplate(widget) {
        // const data = {};
        // data[widget] = {};
        handleTracker.removeField(widget)
        // const endpointURL = '/ads/';
        const dataJSON = JSON.stringify(handleTracker.getState())
        // Получение текущего пути из адресной строки браузера
        const endpointURL = window.location.pathname;
        fetch(endpointURL, {
            method: 'POST',
            body: dataJSON,
            headers: {
                'X-CSRFToken': state.csrfToken,
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
            },
            credentials: 'include',
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const adsContainer = document.querySelector('#ads-container');
                    adsContainer.innerHTML = data.html;
                    // const tbody = state.container.querySelector('tbody');
                    if (widget === 'search') {
                        resetSearchUI();
                    } else if (widget === 'sort') {
                        resetSortUI();
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
    state.sortForm.classList.add('d-none');
    state.sortLabel.classList.add('hide');
    state.sortResetButton.classList.add('d-none');
    state.sortSubmitButton.classList.add('d-none');
    state.filterForm.classList.add('d-none');
    state.fieldSelect.classList.add('d-none');
    state.resetSearchLabel.classList.add('d-none');
    // state.sortLabel.textContent = 'Применена';

    // Обработчики событий

    state.sortToggleButton.addEventListener('click', toggleSortForm);
    state.toggleButtonFilter.addEventListener('click', toggleFilterForm);
    state.sortResetButton.addEventListener('click', () => resetTemplate('sort'));
    state.resetSearchLabel.addEventListener('click', () => resetTemplate('search'));
    //
    state.fieldSelect.addEventListener('change', () => {
        const selectedField = state.fieldSelect.options[state.fieldSelect.selectedIndex];
        if (selectedField && selectedField.value !== '') {  // Проверка, что выбрано не пустое значение
            const {value, text} = selectedField;
            addSortField(value, text);
        }
    });

    state.sortSubmitButton.addEventListener('click', () => {
        state.sortLabel.classList.remove('hide');
        state.sortApplied = true;
        handleTracker.addField('sort', state.sortFields);
        const dataJSON = JSON.stringify(handleTracker.getState());
        // const endpointURL = '/ads/';
        // Получение текущего пути из адресной строки браузера
        const endpointURL = window.location.pathname;
        let url_arr = endpointURL.split('/')
        const salon_id = url_arr[url_arr.length - 2]
        fetch(endpointURL, {
            method: 'POST',
            body: dataJSON,
            headers: {
                'X-CSRFToken': state.csrfToken,
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
            },
            credentials: 'include',
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const adsContainer = document.querySelector('#ads-container');
                    adsContainer.innerHTML = data.html;
                    toggleSortForm();
                    state.sortResetButton.classList.remove('d-none');
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

        if (vinValue === '') {
            handleTracker.removeField('search')
        } else {
            handleTracker.addField('search', vinValue)
        }
        const dataJSON = JSON.stringify(handleTracker.getState())
        // const endpointURL = '/ads/';
        // Получение текущего пути из адресной строки браузера
        const endpointURL = window.location.pathname;
        fetch(endpointURL, {
            method: 'POST',
            body: dataJSON,
            headers: {
                'X-CSRFToken': state.csrfToken,
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
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

    });

    class RenderTemplate {
        constructor(selector) {
            this.adsContainer = document.querySelector(selector);
        }

        // Метод для отрисовки объявлений на основе отфильтрованных данных
        renderAds(filteredData) {
            // Ообновляем контейнер перед добавлением новых объявлений
            this.adsContainer.innerHTML = '';
            // Проходимся по каждому отфильтрованному объявлению и создаем контейнер для него
            filteredData.forEach(ad => {
                const adContainer = this.createAdContainer(ad);
                // Добавляем созданный контейнер(карточку авто) в общий контейнер для объявлений
                this.adsContainer.appendChild(adContainer);
            });
        }

        // Метод для создания карточки объявления
        createAdContainer(ad) {
            const adContainer = document.createElement('div');
            adContainer.className = 'container mt-4';
            // Заполняем карточку данными из переданного объекта ad
            adContainer.innerHTML = `
        <div class="card-ads">
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4">
                        <a href="${ad.absolute_url}" target="_blank" rel="noopener">
                            <img class="img-fluid rounded" src="${ad.first_photo}" alt="${ad}">
                        </a>
                    </div>
                    <div class="col-md-8">
                        <div class="card-title">
                            <a href="${ad.absolute_url}" target="_blank"
                               rel="noopener">${ad.mark_name} <br> ${ad.model_name}</a>
                            <div class="price-container">
                                <div class="card-price">
                                    <span class="detail-price">${ad.price_display}</span>
                                    ${ad.price_nds_display == "Да" ?
                `<span class="sticker nds-yes">с НДС</span>` :
                `<span class="sticker nds-no">без НДС</span>`}

                                </div>
                                <div class="good">
                                    <span class="good-price">${ad.good_price}</span>
                                    <span class="sticker discount">Минимальная</span>
                                </div>
                            </div>
                            <span class="card-year">${ad.year} г</span>
                        </div>
                        <div class="card-text">
                            <p class="card-text__prev text-body-secondary">
                                ${ad.complectation}<br>
                                ${ad.modification_display}  <br>
                                ${ad.body_type} <br>
                                ${ad.color}<br>
                                ${ad.original_vin}<br>

                            </p>
                            <p class="card-text__prev text-body-secondary">
                                ${ad.run_display} <br>
                                ${ad.availability_display}<br>
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
            return adContainer;
        }
    }

// Ообъект FetchData для отправки и получения данных с сервера
    class FetchData {
        constructor() {
            // Объект RenderTemplate для отрисовки страницы
            this.render = new RenderTemplate('#ads-container');
        }

        // Метод для получения данных с сервера в зависимости от выбранных значений фильтров
        async fetchDataSelect(endpoint, urlParam, selectedValues, field) {
            try {
                // Получение текущего пути из адресной строки браузера
                const url = window.location.pathname;
                // Получение ID салона из url
                let url_arr = url.split('/');
                const salonID = url_arr[url_arr.length - 2];
                // Создаем параметры запроса для передачи выбранных фильтров
                const params = new URLSearchParams();
                // Отдельно добавляем каждый параметр, получается ключ-строка: массив
                selectedValues.forEach(value => {
                    params.append(urlParam, value)
                })
                params.append('salon_id', salonID)
                // !! ПЕРЕДАВАТЬ НА API ЭНДПОНИТЫ СОДЕРЖИМОЕ ФИЛЬТРТРЕКЕРА И ЗАПОЛНЯТЬ СЕЛЕКТЫ

                // Отправляем запрос на сервер с учетом выбранных фильтров
                const response = await fetch(`${endpoint}?${params}`);
                if (!response.ok) {
                    throw new Error(`Ошибка запроса: ${response.status}`);
                }
                // Получаем данные с сервера и подготавливаем их к отображению
                let response_data = await response.json();
                return this.data_preparation(response_data, field)
            } catch (error) {
                console.error(`Произошла ошибка при запросе: ${error.message}`);
                throw error;
            }
        }

        // Метод для получения данных с сервера без фильтрации, для изночальных данных
        async fillSelect(url, field) {
            try {
                                // Создаем параметры запроса для передачи выбранных фильтров
                const params = new URLSearchParams();
                // Получение текущего пути из адресной строки браузера
                const current_url = window.location.pathname;
                // Получение ID салона из url
                let url_arr = current_url.split('/');
                const salonID = url_arr[url_arr.length - 2];
                params.append('salon_id', salonID)
                const response = await fetch(`${url}?${params}`);
                if (!response.ok) {
                    throw new Error(`Ошибка запроса: ${response.status}`);
                }
                let response_data = await response.json();
                return this.data_preparation(response_data, field)
            } catch (error) {
                console.error(`Произошла ошибка при запросе: ${error.message}`);
                throw error;
            }
        }

        // Метод для фильтрации объявлений на основе переданных фильтров
        async filterAds(filters) {
            // try {
            //     const url = '/api/filter-ads/';
            //     const params = new URLSearchParams();
            //     console.log(filterTracker.getFilters())
            //     // Добавляем каждый фильтр в параметры запроса
            //     for (const key in filters) {
            //         if (Array.isArray(filters[key]) && filters[key].length > 0) {
            //             filters[key].forEach(value => {
            //                 params.append(key, value);
            //             });
            //         }
            //     }
            //     // Отправляем запрос на сервер для фильтрации объявлений
            //     const filterResponse = await fetch(`${url}?${params}`);
            //
            //     if (!filterResponse.ok) {
            //         throw new Error(`Ошибка фильтрации объявлений: ${filterResponse.status}`);
            //     }
            //
            //     // Получаем отфильтрованные данные
            //     const filteredData = await filterResponse.json();
            //     // и отрисовываем страницу
            //     await this.render.renderAds(filteredData)
            // } catch (error) {
            //     console.error('Произошла ошибка при фильтрации объявлений:', error.message);
            // }
            try {
                // Получение текущего пути из адресной строки браузера
                const url = window.location.pathname;
                // Получение ID салона из url
                let url_arr = url.split('/');
                const salon_id = url_arr[url_arr.length - 2];
                if (Object.keys(filterTracker.state).length) {
                    handleTracker.addField('filters', filterTracker.getFilters());
                } else {
                    handleTracker.removeField('filters');
                }
                // Преобразование объекта фильтров в строку JSON
                let filters = handleTracker.getState();
                filters['salon_id'] = salon_id;
                const filtersJSON = JSON.stringify(filters);
                // Отправляем запрос на сервер для фильтрации объявлений
                const filterResponse = await fetch(url, {
                    method: 'POST',
                    body: filtersJSON,
                    headers: {
                        'X-CSRFToken': state.csrfToken,
                        'Accept': 'application/json, text/plain, */*',
                        'Content-Type': 'application/json',
                    },
                    credentials: 'include',
                });

                if (!filterResponse.ok) {
                    throw new Error(`Ошибка фильтрации объявлений: ${filterResponse.status}`);
                }

                // Получаем отфильтрованные данные
                const filteredData = await filterResponse.json();
                const adsContainer = document.querySelector('#ads-container');
                adsContainer.innerHTML = filteredData.html;
                // и отрисовываем страницу
                // await this.render.renderAds(filteredData);
            } catch (error) {
                console.error('Произошла ошибка при фильтрации объявлений:', error.message);
            }
        }

        // Метод для подготовки данных к отображению в виде объекта со значениями и метками
        data_preparation(data, field) {
            return data.map(item => ({
                value: item.id !== undefined ? item.id : item[field],
                label: item[field],
            }));
        }
    }

// Базовый класс для управления селектами
    class SelectManager {
        constructor(selector, field) {
            this.selector = document.querySelector(selector);
            // Объект FetchData для обработки запросов с сервера
            this.handlerFetch = new FetchData()
            // Устанавливаем поле, по которому будет происходить фильтрация
            this.field = field;
            // Создаем экземпляр Choices для работы с выбором в селекте
            this.choices = new Choices(this.selector, {
                choices: [],
                placeholder: true,
                searchEnabled: true,
                removeItemButton: true,
                allowHTML: true,
                resetScrollPosition: false,
                noResultsText: 'Ничего не найдено',
                itemSelectText: '',
                noChoicesText: '',
            });

        }

        // Метод для обновления значений фильтров на основе выбора
        updateFiltersValues() {
            const selectedValues = this.choices.getValue(true);
            filterTracker.addFilter(this.field, selectedValues)
            console.log(filterTracker)
            if (filterTracker.state[this.field].length === 0) {
                filterTracker.removeFilter(this.field)
            }
        }

        // Метод для инициализации(заполнения) данных в селекте
        initData(select, data) {
            select.clearChoices()
            select.setChoices(data)
            select.enable()
        }

        // Метод для очистки селекта и удаления фильтра
        clearSelect(select) {
            // filterTracker.removeFilter(this.field)
            select.hideDropdown()
            select.clearStore()
            select.disable()
        }
    }

// Класс для работы с выбором марок
    class MarkSelect extends SelectManager {
        constructor(selector) {
            super(selector, 'marks');
            this.initAsync(() => this.fetchFillData());
        }

        // Метод для инициализации данных
        initAsync(initCallback) {
            initCallback().then(() => {
                this.addEventListeners().then(() => console.log("События отработали")
                )
                ;
            });
        }

        // Метод для получения данных о марках с сервера
        async fetchFillData() {
            let data = await this.handlerFetch.fillSelect('/ads/api/marks/', 'name')
            this.initData(this.choices, data)
        }

        // Метод для очистки селекта марок
        clearSelect(select) {
            super.clearSelect(select);
        }

        // Метод для добавления событий изменения выбора марок
        async addEventListeners() {
            this.selector.addEventListener('change', async (event) => {
                await this.updateFiltersValues()

                if (filterTracker.state['marks']) {
                    // При выборе марки заполняется поле с моделями авто т.к. оно зависимо
                    selects.modelSelect.fetchFillData()
                } else {
                    // Если нет выбранных марок, отключаем и очищаем все селекты моделей и сбрасываем фильтры
                    this.clearSelect(selects.modelSelect.choices)
                    this.clearSelect(selects.complectationSelect.choices)
                    this.clearSelect(selects.modificationSelect.choices)
                    this.clearSelect(selects.colorSelect.choices)
                    this.clearSelect(selects.bodySelect.choices)
                    filterTracker.clearFilters()
                    handleTracker.removeField('filters')
                }
                await this.handlerFetch.filterAds(filterTracker.getFilters())
            })
        }
    }

// Класс для работы с выбором моделей
    class ModelSelect extends SelectManager {
        constructor(selector) {
            super(selector, 'models');
            this.choices.disable()
            this.addEventListeners()

        }

        // Метод для получения данных о моделях с сервера в зависимости от выбранных марок
        async fetchFillData() {
            let data = await this.handlerFetch.fetchDataSelect(
                '/ads/api/models/', 'marks', filterTracker.state['marks'], 'name'
            );
            this.initData(this.choices, data)
        }

        // Метод для очистки селекта моделей
        clearSelect(select) {
            super.clearSelect(select);
        }

        // Метод для добавления событий изменения выбора моделей
        async addEventListeners() {
            this.selector.addEventListener('change', async (event) => {
                await this.updateFiltersValues()

                if (filterTracker.state['models']) {
                    // При выборе модели заполняются поля с модификацией, цветом, кузовом и т.д, т.к. оно зависимы
                    selects.modificationSelect.fetchFillData()
                    selects.bodySelect.fetchFillData()
                    selects.complectationSelect.fetchFillData()
                    selects.colorSelect.fetchFillData()

                } else {
                    // Если нет выбранных моделей, очищаем селекты модификаций, типов кузова, конфигураций и цветов и фильтры
                    selects.modificationSelect.clearSelect(selects.modificationSelect.choices)
                    selects.bodySelect.clearSelect(selects.bodySelect.choices)
                    selects.complectationSelect.clearSelect(selects.complectationSelect.choices)
                    selects.colorSelect.clearSelect(selects.colorSelect.choices)
                }

                await this.handlerFetch.filterAds(filterTracker.getFilters())
            });
        }
    }

// Класс для работы с выбором модификаций
    class ModificationSelect extends SelectManager {
        constructor(selector) {
            super(selector, 'modifications');
            this.choices.disable()
            this.addEventListeners()

        }

        // Метод для получения данных о модификациях с сервера в зависимости от выбранных моделей
        async fetchFillData() {
            const selectedModels = filterTracker.state['models']

            let dataModifications = await this.handlerFetch.fetchDataSelect(
                '/ads/api/modifications/', 'models', selectedModels, 'modification_display'
            )
            this.initData(this.choices, dataModifications)
        }

        // Метод для очистки селекта модификаций
        clearSelect(select) {
            super.clearSelect(select);
        }

        // Метод для добавления событий изменения выбора модификаций
        async addEventListeners() {
            this.selector.addEventListener('change', async (event) => {
                this.updateFiltersValues()
                await this.handlerFetch.filterAds(filterTracker.getFilters())
            });
        }
    }

// Класс для работы с выбором типов кузова
    class BodySelect extends SelectManager {
        constructor(selector) {
            super(selector, 'bodies');
            this.choices.disable()
            this.addEventListeners()

        }

        // Метод для получения данных о типах кузова с сервера  в зависимости от выбранных моделей
        async fetchFillData() {
            const selectedModels = filterTracker.state['models']

            let dataBodies = await this.handlerFetch.fetchDataSelect(
                '/ads/api/bodies/', 'models', selectedModels, 'body_type'
            )
            this.initData(this.choices, dataBodies)
        }

        // Метод для очистки селекта типов кузова
        clearSelect(select) {
            super.clearSelect(select);
        }

        // Метод для добавления событий изменения выбора типов кузова
        async addEventListeners() {
            this.selector.addEventListener('change', async (event) => {
                this.updateFiltersValues()
                await this.handlerFetch.filterAds(filterTracker.getFilters())
            });
        }
    }

// Класс селекта с выбором комплектации
    class ComplectationSelect extends SelectManager {
        constructor(selector) {
            super(selector, 'complectations');
            this.choices.disable()
            this.addEventListeners()
        }

        // Метод для получения данных о конфигурациях с сервера  в зависимости от выбранных моделей
        async fetchFillData() {
            const selectedModels = filterTracker.state['models']

            let dataModifications = await this.handlerFetch.fetchDataSelect(
                '/ads/api/complectations/', 'models', selectedModels, 'complectation'
            )
            this.initData(this.choices, dataModifications)
        }

        // Метод для очистки селекта конфигураций
        clearSelect(select) {
            super.clearSelect(select);
        }

        // Метод для добавления событий изменения выбора конфигураций
        async addEventListeners() {
            this.selector.addEventListener('change', async (event) => {
                this.updateFiltersValues()
                await this.handlerFetch.filterAds(filterTracker.getFilters())
            });
        }

    }

// Класс для работы с выбором цветов автомобилей
    class ColorSelect extends SelectManager {
        constructor(selector) {
            super(selector, 'colors');
            this.choices.disable()
            this.addEventListeners()

        }

        // Метод для получения данных о цветах с сервера  в зависимости от выбранных моделей
        async fetchFillData() {
            const selectedModels = filterTracker.state['models']

            let dataColors = await this.handlerFetch.fetchDataSelect(
                '/ads/api/colors/', 'models', selectedModels, 'color'
            )
            this.initData(this.choices, dataColors)
        }

        // Метод для очистки селекта цветов
        clearSelect(select) {
            super.clearSelect(select);
        }

        // Метод для добавления событий изменения выбора цветов
        async addEventListeners() {
            this.selector.addEventListener('change', async (event) => {
                this.updateFiltersValues()
                await this.handlerFetch.filterAds(filterTracker.getFilters())
            });
        }
    }

// Глобальный объект для хранения ссылок на селекты
    const selects = {
        markSelect: null,
        modelSelect: null,
        modificationSelect: null,
        bodySelect: null,
        complectationSelect: null,
        colorSelect: null,


    };

// Объект для отслеживания выбранных фильтров
    const filterTracker = {
        state: {},

        // Метод для добавления фильтра
        addFilter(field, values) {
            if (field)
                this.state[field] = values;
        },

        // Метод для удаления фильтра
        removeFilter(field) {
            if (field in this.state) {
                delete this.state[field]
            } else {
                console.error(`Фильтр с полем ${field} не существует.`);
            }
        },

        // Метод для получения выбранных фильтров
        getFilters() {
            return this.state;
        },
        // Метод для очистки всех выбранных фильтров
        clearFilters() {
            this.state = {}
        }
    };

// Создаем экземпляр FetchData для обработки запросов с сервера
    const fetchData = new FetchData();

// Находим все поля ввода и чекбокс
    const priceFromInput = document.querySelector('.input-from.price-input');
    const priceToInput = document.querySelector('.input-to.price-input');
    const yearFromInput = document.querySelector('.input-from.year-input');
    const yearToInput = document.querySelector('.input-to.year-input');
    const runFromInput = document.querySelector('.input-from.run-input');
    const runToInput = document.querySelector('.input-to.run-input');
// const mileageCheckbox = document.querySelector('#checkbox-rect2');

// Устанавливаем ссылки на созданные селекты в глобальном объекте
    selects.markSelect = new MarkSelect('.mark-select');
    selects.modelSelect = new ModelSelect('.model-select');
    selects.modificationSelect = new ModificationSelect('.modification-select');
    selects.bodySelect = new BodySelect('.body-select');
    selects.complectationSelect = new ComplectationSelect('.complectation-select');
    selects.colorSelect = new ColorSelect('.color-select');


// Добавляем обработчики событий для полей ввода и чекбокса
    priceFromInput.addEventListener('input', async () => {
        await sendFilterData('priceFrom', priceFromInput);
        togglePlaceholderSize(priceFromInput);
    });

    priceToInput.addEventListener('input', async () => {
        await sendFilterData('priceTo', priceToInput);
        togglePlaceholderSize(priceToInput);
    });

    yearFromInput.addEventListener('input', async () => {
        await sendFilterData('yearFrom', yearFromInput);
        togglePlaceholderSize(yearFromInput);
    });

    yearToInput.addEventListener('input', async () => {
        await sendFilterData('yearTo', yearToInput);
        togglePlaceholderSize(yearToInput);
    });

    runFromInput.addEventListener('input', async () => {
        await sendFilterData('runFrom', runFromInput);
        togglePlaceholderSize(runFromInput);
    });

    runToInput.addEventListener('input', async () => {
        await sendFilterData('runTo', runToInput);
        togglePlaceholderSize(runToInput);
    });

// Функция для изменения размера кастомного плейсхолдера в зависимости от состояния инпута
    function togglePlaceholderSize(input) {
        const placeholder = input.nextElementSibling;
        if (input.value.trim()) {
            placeholder.classList.add('focused');
        } else {
            placeholder.classList.remove('focused');
        }
    }

    async function sendFilterData(field, inputObject) {
        try {
            const priceFromValue = [inputObject.value]
            if (inputObject.value !== '') {
                filterTracker.addFilter(field, priceFromValue)
            } else {
                filterTracker.removeFilter(field)
            }
            // Отправка данных на сервер
            await fetchData.filterAds(filterTracker.getFilters());
        } catch (error) {
            console.error('Произошла ошибка при отправке фильтров:', error.message);
        }
    }

    function exportXml() {
        // Получить все элементы с классом "col-lg-12"
        const cardElements = document.getElementsByClassName("col-lg-12");

        // Создать массив для хранения идентификаторов
        const ids = [];

        // Пройти по каждому элементу и получить значение атрибута data-id
        for (let i = 0; i < cardElements.length; i++) {
            const cardElement = cardElements[i];
            const id = cardElement.getAttribute("data-id");

            // Добавить значение id в массив
            ids.push(id);
        }
        console.log(ids)

        // Создаем параметры запроса для передачи выбранных идентификаторов
        const params = new URLSearchParams();

        // Добавляем идентификаторы в параметры запроса
        ids.forEach(id => {
            params.append('id', id);
        });

        // Получить CSRF-токен
        const csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
        // Отправить запрос на бэкенд с параметрами URL
        fetch(`/ads/api/export-xml/?${params.toString()}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json',
            },
            credentials: 'include',
        })
            .then(response => response.blob())
            .then(blob => {
                // Создать ссылку на файл XML
                console.log(blob.text())
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = "exported_ads.xml";
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            })
            .catch(error => console.error('Ошибка при экспорте объявлений:', error));
    }

    document.getElementById('export-xml-button').addEventListener('click', exportXml);
})
;
