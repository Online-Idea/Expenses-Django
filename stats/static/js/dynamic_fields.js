// Для полей которые зависят от родительских полей
document.addEventListener('DOMContentLoaded', function() {
  document.querySelector('#id_mark').addEventListener('change', updateModelOptions);
  updateModelOptions();
});

function updateModelOptions() {
  const markField = document.querySelector('#id_mark');
  const modelField = document.querySelector('#id_model');
  const selectedMark = markField.value;
  fetch(`/api/get_models_for_mark/${selectedMark}/`)
    .then(response => response.json())
    .then(models => {
      modelField.innerHTML = '';
      models.forEach(model => {
        const option = document.createElement('option');
        option.value = model.id;
        option.text = model.model;
        modelField.add(option);
      });
    });
}
