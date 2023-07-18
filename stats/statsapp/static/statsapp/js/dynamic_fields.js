// Для полей которые зависят от родительских полей
document.addEventListener('DOMContentLoaded', function() {
    const markField = document.querySelector('#id_mark');
    const modelField = document.querySelector('#id_model');

    function updateModelOptions() {
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

    markField.addEventListener('change', updateModelOptions);
    updateModelOptions();
});
