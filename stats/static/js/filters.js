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
        <div class="card">
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
                                ${ad.configuration}<br>
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

// Глобальный объект для хранения ссылок на селекты
const selects = {
    colorSelect: null,
    configurationSelect: null,
    bodySelect: null,
    modificationSelect: null,
    modelSelect: null,
    markSelect: null,
};

// Ообъект FetchData для отправки и получения данных с сервера
class FetchData {
    constructor() {
        // Объект RenderTemplate для отрисовки страницы
        this.render = new RenderTemplate('#ads-container');
    }

    // Метод для получения данных с сервера в зависимости от выбранным значений фильтров
    async fetchDataSelect(endpoint, urlParam, selectedValues, field) {
        try {
            // Создаем параметры запроса для передачи выбранных фильтров
            const params = new URLSearchParams();
            // Отдельно добавляем каждый параметр, получается ключ-строка: массив
            selectedValues.forEach(value => {
                params.append(urlParam, value)
            })

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
            const response = await fetch(url);
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
        try {
            const url = '/api/filter-ads/';
            const params = new URLSearchParams();
            // Добавляем каждый фильтр в параметры запроса
            for (const key in filters) {
                if (Array.isArray(filters[key]) && filters[key].length > 0) {
                    filters[key].forEach(value => {
                        params.append(key, value);
                    });
                }
            }
            // Отправляем запрос на сервер для фильтрации объявлений
            const filterResponse = await fetch(`${url}?${params}`);

            if (!filterResponse.ok) {
                throw new Error(`Ошибка фильтрации объявлений: ${filterResponse.status}`);
            }

            // Получаем отфильтрованные данные
            const filteredData = await filterResponse.json();
            // и отрисовываем страницу
            await this.render.renderAds(filteredData)
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

// Объект для отслеживания выбранных фильтров
const filterTracker = {
    selectedMarks: [],
    selectedModels: [],
    selectedModifications: [],
    selectedBodies: [],
    selectedConfigurations: [],
    selectedColors: [],
    selectedPriceFrom: [],
    selectedPriceTo: [],

    // Метод для добавления фильтра
    addFilter(field, values) {
        this[field] = values;
    },

    // Метод для удаления фильтра
    removeFilter(field) {
        if (field in this) {
            this[field] = [];
        } else {
            console.error(`Фильтр с полем ${field} не существует.`);
        }
    },

    // Метод для получения выбранных фильтров
    getFilters() {
        return {
            marks: this.selectedMarks,
            models: this.selectedModels,
            modifications: this.selectedModifications,
            bodies: this.selectedBodies,
            configurations: this.selectedConfigurations,
            colors: this.selectedColors,
            priceFrom: this.selectedPriceFrom

        };
    },

    // Метод для очистки всех выбранных фильтров
    clearFilters() {
        this.selectedMarks = [];
        this.selectedModels = [];
        this.selectedModifications = [];
        this.selectedBodies = [];
        this.selectedConfigurations = [];
        this.selectedColors = [];
    }
};

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
    async updateFiltersValues() {
        const selectedValues = this.choices.getValue(true);
        await filterTracker.addFilter(this.field, selectedValues)
    }

    // Метод для инициализации(заполнения) данных в селекте
    initData(select, data) {
        select.clearChoices()
        select.setChoices(data)
        select.enable()
    }

    // Метод для очистки селекта и удаления фильтра
    clearSelect(select) {
        filterTracker.removeFilter(this.field)
        select.hideDropdown()
        select.clearStore()
        select.disable()
    }
}

// Класс для работы с выбором марок
class MarkSelect extends SelectManager {
    constructor(selector) {
        super(selector, 'selectedMarks');
        this.initAsync(() => this.fetchFillData());
    }

    // Метод для инициализации данных с последующим добавлением событий
    initAsync(initCallback) {
        initCallback().then(() => {
            this.addEventListeners().then(() => console.log("События отработали")
            )
            ;
        });
    }

    // Метод для получения данных о марках с сервера
    async fetchFillData() {
        let data = await this.handlerFetch.fillSelect('/api/marks/', 'mark')
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

            if (filterTracker.selectedMarks.length > 0) {
                // При выборе марки заполняется поле с моделями авто т.к. оно зависимо
                selects.modelSelect.fetchFillData()
            } else {
                // Если нет выбранных марок, отключаем и очищаем все селекты моделей и сбрасываем фильтры
                this.clearSelect(selects.modelSelect.choices)
                this.clearSelect(selects.configurationSelect.choices)
                this.clearSelect(selects.modificationSelect.choices)
                this.clearSelect(selects.colorSelect.choices)
                this.clearSelect(selects.bodySelect.choices)
                filterTracker.clearFilters()
            }
            await this.handlerFetch.filterAds(filterTracker.getFilters())
        })
    }
}

// Класс для работы с выбором моделей
class ModelSelect extends SelectManager {
    constructor(selector) {
        super(selector, 'selectedModels');
        this.choices.disable()
        this.addEventListeners()

    }

    // Метод для получения данных о моделях с сервера в зависимости от выбранных марок
    async fetchFillData() {
        let data = await this.handlerFetch.fetchDataSelect(
            '/api/models/', 'marks', filterTracker.selectedMarks, 'model'
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

            if (filterTracker.selectedModels.length > 0) {
                // При выборе модели заполняются поля с модификацией, цветом, кузовом и т.д, т.к. оно зависимы
                selects.modificationSelect.fetchFillData()
                selects.bodySelect.fetchFillData()
                selects.configurationSelect.fetchFillData()
                selects.colorSelect.fetchFillData()

            } else {
                // Если нет выбранных моделей, очищаем селекты модификаций, типов кузова, конфигураций и цветов и фильтры
                selects.modificationSelect.clearSelect(selects.modificationSelect.choices)
                selects.bodySelect.clearSelect(selects.bodySelect.choices)
                selects.configurationSelect.clearSelect(selects.configurationSelect.choices)
                selects.colorSelect.clearSelect(selects.colorSelect.choices)
            }

            await this.handlerFetch.filterAds(filterTracker.getFilters())
        });
    }
}

// Класс для работы с выбором модификаций
class ModificationSelect extends SelectManager {
    constructor(selector) {
        super(selector, 'selectedModifications');
        this.choices.disable()
        this.addEventListeners()

    }

    // Метод для получения данных о модификациях с сервера в зависимости от выбранных моделей
    async fetchFillData() {
        const selectedModels = filterTracker.selectedModels

        let dataModifications = await this.handlerFetch.fetchDataSelect(
            '/api/modifications/', 'models', selectedModels, 'modification_display'
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
            await this.updateFiltersValues()
            await this.handlerFetch.filterAds(filterTracker.getFilters())

        });
    }
}

// Класс для работы с выбором типов кузова
class BodySelect extends SelectManager {
    constructor(selector) {
        super(selector, 'selectedBodies');
        this.choices.disable()
        this.addEventListeners()

    }

    // Метод для получения данных о типах кузова с сервера  в зависимости от выбранных моделей
    async fetchFillData() {
        const selectedModels = filterTracker.selectedModels

        let dataBodies = await this.handlerFetch.fetchDataSelect(
            '/api/bodies/', 'models', selectedModels, 'body_type'
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
            await this.updateFiltersValues()
            await this.handlerFetch.filterAds(filterTracker.getFilters())

        });
    }
}

// Класс селекта с выбором комплектации
class ConfigurationSelect extends SelectManager {
    constructor(selector) {
        super(selector, 'selectedConfigurations');
        this.choices.disable()
        this.addEventListeners()
    }

    // Метод для получения данных о конфигурациях с сервера  в зависимости от выбранных моделей
    async fetchFillData() {
        const selectedModels = filterTracker.selectedModels

        let dataModifications = await this.handlerFetch.fetchDataSelect(
            '/api/configurations/', 'models', selectedModels, 'configuration'
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
            await this.updateFiltersValues()
            await this.handlerFetch.filterAds(filterTracker.getFilters())

        });
    }

}

// Класс для работы с выбором цветов автомобилей
class ColorSelect extends SelectManager {
    constructor(selector) {
        super(selector, 'selectedColors');
        this.choices.disable()
        this.addEventListeners()

    }

    // Метод для получения данных о цветах с сервера  в зависимости от выбранных моделей
    async fetchFillData() {
        const selectedModels = filterTracker.selectedModels

        let dataColors = await this.handlerFetch.fetchDataSelect(
            '/api/colors/', 'models', selectedModels, 'color'
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
            await this.updateFiltersValues()
            await this.handlerFetch.filterAds(filterTracker.getFilters())

        });
    }
}


// Обработчик события загрузки DOM-дерева
document.addEventListener('DOMContentLoaded', () => {

    // Устанавливаем ссылки на созданные селекты в глобальном объекте
    selects.markSelect = new MarkSelect('.mark-select');
    selects.modelSelect = new ModelSelect('.model-select');
    selects.modificationSelect = new ModificationSelect('.modification-select');
    selects.bodySelect = new BodySelect('.body-select');
    selects.configurationSelect = new ConfigurationSelect('.configuration-select');
    selects.colorSelect = new ColorSelect('.color-select');
});

