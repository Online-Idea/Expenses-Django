document.addEventListener('DOMContentLoaded', () => {
    let expandTrigger = document.querySelector('.expand-trigger');
    let modificationFields = document.querySelectorAll('.field-name .modification-field, ' +
        '.field-value .modification-field');
    let modificationPreview = document.querySelector('.field-value .modification-preview');
    let photos = document.querySelector('.references-photos');
    let referencesTrigger = document.querySelector('.references-trigger');

    let codesTrigger = document.querySelector('.codes-trigger');
    let codes = document.querySelector('.description-codes');

    expandTrigger.addEventListener('click', () => {
        modificationFields.forEach(field => {
            field.classList.toggle('hidden');
        });

        modificationPreview.classList.toggle('hidden-preview');
        modificationPreview.classList.toggle('reveal');
        expandTrigger.classList.toggle('reveal');
    });

    referencesTrigger.addEventListener('click', () => {
        referencesTrigger.classList.toggle('reveal');
        photos.classList.toggle('hidden');
    });

    codesTrigger.addEventListener('click', () => {
        codesTrigger.classList.toggle('reveal');
        codes.classList.toggle('hidden')
    });

});