/*----------------Автоконвертер--------------*/
// Показывает гифку загрузки, отключает кнопку Запустить
function showLoading() {
    const converterSubmit = document.getElementById('submit-id-submit');
    const spinner = document.getElementById('loading-spinner');
    converterSubmit.setAttribute('disabled', '');
    spinner.classList.remove('d-none');
    return 0;
}
/*---------------------------------------------------*/
