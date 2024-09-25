function setSelected(originalSelect, cloneSelect) {
  // Выбирает в клоне те же опции что и в оригинале

  // Если у клона по какой-то причине нет опций то беру их из оригинала
  if (cloneSelect.innerHTML === '') {
    cloneSelect.innerHTML = originalSelect.innerHTML;
  }

  // Если у select элемента выбрана только одна опция
  if (!originalSelect.multiple) {
    cloneSelect.value = originalSelect.value;
    return
  }

  // Если у select элемента выбрано несколько опций
  for (let i = 0; i < originalSelect.options.length; i++) {
    if (originalSelect.options[i].selected) {
      cloneSelect.options[i].selected = true;
    }
  }
}

function dispatchChangeEvent(element) {
  // Отправляет event 'change'
  let event = new Event('change');
  element.dispatchEvent(event);
}

function populateValues(originalElement, newIdNumber) {
  // Наполняет поля клона данными из оригинала
  for (let i = 0; i < originalElement.children.length; i++) {
    let originalChild = originalElement.children[i];

    // Если у ребёнка нет id значит сначала проверяю его детей и потом перехожу к следующему
    if (!originalChild.hasAttribute('id')) {
      populateValues(originalChild, newIdNumber);
      continue;
    }

    // Нахожу клон по id оригинала, меняя у id оригинала номер на newIdNumber
    let originalId = originalChild.id;
    let cloneIdArray = originalId.split('-');
    cloneIdArray[1] = newIdNumber;
    let cloneId = cloneIdArray.join('-');
    let cloneChild = document.querySelector(`#${cloneId}`);

    // Если у ребёнка есть value то меняю его
    if (originalChild.hasAttribute('value')) {
      // cloneChild.value = originalChild.value;
      cloneChild.setAttribute('value', originalChild.value);
      dispatchChangeEvent(cloneChild);

      // Если ребёнок это <select> значит вызываю setSelected
    } else if (originalChild.tagName === 'SELECT') {
      setSelected(originalChild, cloneChild);
      dispatchChangeEvent(cloneChild);

      // Иначе прохожу по его детям
    } else {
      populateValues(originalChild, newIdNumber);
    }
  }
}

function duplicateInline(event) {
  /**
   * Кнопка Дублировать для inline в админ панели Django.
   * Чтобы эту кнопку добавить, в классе inline добавь:
   * readonly_fields = ('duplicate_button', )
   * def duplicate_button(self, obj):
   *     return format_html('<button type="button" onclick="duplicateInline(this);"><i class="fa-solid fa-copy"></i></button>')
   * duplicate_button.short_description = 'Дублировать'
   * И подключи этот файл в Media класса ModelAdmin
   * class Media:
   *    js = ('js/duplicate_inline.js', )
   */
  // tr и id от inline который собираюсь дублировать
  const row = event.closest('tr');
  const currId = row.id;
  // tbody именно этого inline класса
  const tbody = row.closest('tbody');

  // Новый id для дубля
  let idArray = currId.split('-');
  const inlineName = idArray[0];
  const totalRows = tbody.querySelectorAll(`tr.dynamic-${inlineName}`).length;
  idArray[idArray.length - 1] = totalRows;
  const newId = idArray.join('-');

  // Жму кнопку Django "Добавить ещё один inline"
  const addButtonTr = tbody.querySelector('.add-row');
  const addButton = addButtonTr.querySelector('a');
  addButton.click();

  const newRow = document.querySelector(`#${newId}`);
  // Заполняю значения полей в дубле значениями из оригинала
  populateValues(row, totalRows);

  eventListenersForDynamicFields();

}
