// Для полей которые зависят от родительских полей
document.addEventListener('DOMContentLoaded', eventListenersForDynamicFields);
document.addEventListener('formset:added', eventListenersForDynamicFields);

const callPriceSettingsPrefix = 'call_price_settings';

function eventListenersForDynamicFields(event) {
  modelFromMark();
  callPriceSettingAvailability();
}

function modelFromMark() {
  // Наполняет Модель в зависимости от Марки
  const rows = collectRows();

  if (!rows[0]) {
    return;
  }

  // Уникальные Марки
  let uniqueMarksWithModels = {};
  rows.forEach(row => {
    const markElement = row.querySelector('[id^="id"][id$="mark"]');
    if (markElement && markElement.value) {
      const markValue = String(markElement.value);
      if (!(markValue in uniqueMarksWithModels)) {
        uniqueMarksWithModels[markValue] = null;
      }
    }
  });
  // Модели для Марок
  Promise.all(
    Object.keys(uniqueMarksWithModels).map(key =>
      fetch(`/api/get_models_for_mark/${key}/`)
        .then(response => response.json())
        .then(models => {
          uniqueMarksWithModels[key] = models;
          return models;
        })
    )
  ).then(() => {
    // Наполняю Модели
    for (const row of rows) {
      const markField = row.querySelector('[id^="id"][id$="mark"]');
      let modelField = row.querySelector('[id^="id"][id$="model"]');

      if (!markField && !modelField) {
        continue;
      }

      // Wrap the event listener attachment in a closure to capture the current state of mark and modelField
      (function (markField, modelField, uniqueMarksWithModels) {
        markField.addEventListener('change', () => updateModelOptions(markField, modelField, uniqueMarksWithModels));
      })(markField, modelField, uniqueMarksWithModels);

      // Directly call updateModelOptions with the current markField and modelField
      updateModelOptions(markField, modelField, uniqueMarksWithModels);
    }
  }).catch(error => {
    console.log(error);
  });
}

function collectRows() {
  // Собирает родительские элементы
  // Для страницы где есть CallPriceSetting
  // let rows = document.querySelectorAll('tr[id^="call_price_settings"]');
  let rows = document.querySelectorAll(`#${callPriceSettingsPrefix}-group tbody tr`);
  if (!rows[0]) {
    // Для страницы где используется модальное окно
    rows = [document.querySelector('.modal-body')];
  }
  return rows;
}

function populateOptions(uniqueMarksWithModels, selectedMark, modelField) {
  uniqueMarksWithModels[selectedMark].forEach(model => {
    const option = document.createElement('option');
    option.value = model.id;
    option.text = model.model;
    modelField.add(option);
  });
}

function updateModelOptions(markField, modelField, uniqueMarksWithModels) {
  const selectedMark = markField.value;

  // Если Марка не выбрана то в Моделях пусто
  if (!selectedMark) {
    modelField.innerHTML = '';
    return
  }

  const selectedModel = modelField.value;

  modelField.innerHTML = '';
  // Опция "не выбрано"
  const emptyOption = document.createElement('option');
  emptyOption.value = '';
  emptyOption.text = '---------';
  modelField.add(emptyOption);

  if (uniqueMarksWithModels[selectedMark]) {
    populateOptions(uniqueMarksWithModels, selectedMark, modelField);
  } else {
    fetch(`/api/get_models_for_mark/${selectedMark}`, )
      .then(response => response.json())
      .then(models => {
        uniqueMarksWithModels[selectedMark] = models;
        populateOptions(uniqueMarksWithModels, selectedMark, modelField);
      });
  }

  // Выбираю ранее выбранную Модель
  modelField.value = selectedModel ? selectedModel : '';
}


/*
function updateModelOptions(markField, modelField) {
  // Готовит опции для Моделей
  const selectedMark = markField.value;

  // Если Марка не выбрана то в Моделях пусто
  if (!selectedMark) {
    modelField.innerHTML = '';
    return
  }

  const selectedModel = modelField.value;

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

      // Выбираю ранее выбранную Модель
      modelField.value = selectedModel ? selectedModel : '';
    });
}
*/


function buildSelector(fieldName) {
  return `[id^="id_${callPriceSettingsPrefix}"][id$="${fieldName}"]`;
}

function callPriceSettingAvailability() {
  // Переключает возможность менять поля для модели CallPriceSetting в зависимости от Типа (charge_type)
  const chargeTypeSelector = buildSelector('charge_type');
  const rows = collectRows();

  if (!rows[0]) {
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
