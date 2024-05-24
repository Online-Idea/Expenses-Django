// Для полей которые зависят от родительских полей
document.addEventListener('DOMContentLoaded', eventListenersForDynamicFields);
document.addEventListener('formset:added', eventListenersForDynamicFields);

function eventListenersForDynamicFields(event) {
  modelFromMark();
  callPriceSettingAvailability();
}

function collectRows(childElementSelector) {
  // Собирает родительские элементы
  const children = document.querySelectorAll(childElementSelector);
  let rows = Array.from(children)
    .map(child => child.closest('tr'))
    .filter(row => row !== null);
  if (!rows[0]) {
    rows = [$('.modal-body')];
  }
  return rows;
}


function modelFromMark() {
  // Наполняет Модель в зависимости от Марки
  // const rows = collectRows('[id^="id"][id$="mark"]');
  const rows = document.querySelectorAll('tr[id^="call_price_settings"]');

  // if (!rows) {
  //   return;
  // }

  let markField, modelField;
  for (const row of rows) {
    markField = row.querySelector('[id^="id"][id$="mark"]');
    modelField = row.querySelector('[id^="id"][id$="model"]');

    if (markField && modelField) {
      // Wrap the event listener attachment in a closure to capture the current state of mark and modelField
      (function (markField, modelField) {
        markField.addEventListener('change', () => updateModelOptions(markField, modelField));
      })(markField, modelField);

      // Directly call updateModelOptions with the current mark and modelField
      if (modelField.value === '') {
        updateModelOptions(markField, modelField);
      } // TODO если Модель выбрана то всё равно вызови updateModelOptions чтобы подтянуть Модели текущей Марки и потом программно выбрать уже выбранную Модель
    }
  }
}


function updateModelOptions(markField, modelField) {
  // Готовит опции для Моделей
  const selectedMark = markField.value;

  // Если Марка не выбрана то в Моделях пусто
  if (!selectedMark) {
    modelField.innerHTML = '';
    return
  }

  // Запрос к базе чтобы получить Модели от Марки
  fetch(`/api/get_models_for_mark/${selectedMark}/`)
    .then(response => response.json())
    .then(models => {
      modelField.innerHTML = '';
      // Опция "не выбрано"
      const emptyOption = document.createElement('option');
      emptyOption.value = '';
      emptyOption.text = '---------';
      modelField.add(emptyOption);

      models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.text = model.model;
        modelField.add(option);
      });
    });
}


const callPriceSettingsPrefix = 'id_call_price_settings';

function buildSelector(fieldName) {
  return `[id^="${callPriceSettingsPrefix}"][id$="${fieldName}"]`;
}

function callPriceSettingAvailability() {
  // Переключает возможность менять поля для модели CallPriceSetting в зависимости от Типа (charge_type)
  const chargeTypeSelector = buildSelector('charge_type');
  const rows = collectRows(chargeTypeSelector);

  if (!rows) {
    return;
  }

  for (const row of rows) {
    const chargeTypeField = row.querySelector(chargeTypeSelector);

    // Listen for changes
    (function (chargeTypeField, row) {
      chargeTypeField.addEventListener('change', () => updateFieldsAvailability(row));
    })(chargeTypeField, row);

    // Initial check
    updateFieldsAvailability(row);
  }
}


function updateFieldsAvailability(row) {
  // Переключает возможность менять поля
  const chargeTypeValue = row.querySelector(buildSelector('charge_type')).value;
  const fields = {
    moderation: row.querySelector(buildSelector('moderation')),
    mark: row.querySelector(buildSelector('mark')),
    model: row.querySelector(buildSelector('model')),
  };

  const disablingRules = {
    '': {},
    'Модель': {},
    'Марка': { model: fields.model },
    'Модерация': { mark: fields.mark, model: fields.model },
    // 'Общая': { moderation: fields.moderation, mark: fields.mark, model: fields.model },
    'Общая': { mark: fields.mark, model: fields.model },
  };

  const rules = disablingRules[chargeTypeValue] || {}; // Use empty object if key not found

  Object.entries(rules).forEach(([fieldName, field]) => {
    field.disabled = true;
  });

  Object.entries(fields).forEach(([fieldName, field]) => {
    if (!rules[fieldName]) {
      field.disabled = false;
    }
  });
}
