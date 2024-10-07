// document.getElementById('export-xml-button').addEventListener('click', function () {
//     const dataJSON = JSON.stringify(handleTracker.getState()); // handleTracker - это ваш объект с текущими фильтрами
//     fetch('/path/to/export/xml/', {
//         method: 'POST',
//         body: dataJSON,
//         headers: {
//             'X-CSRFToken': document.querySelector('input[name="csrfmiddlewaretoken"]').value,
//             'Accept': 'application/json, text/plain, */*',
//             'Content-Type': 'application/json',
//         },
//         credentials: 'include',
//     })
//         .then(response => response.blob())
//         .then(blob => {
//             const url = window.URL.createObjectURL(blob);
//             const a = document.createElement('a');
//             a.href = url;
//             a.download = "exported_ads.xml";
//             document.body.appendChild(a);
//             a.click();
//             window.URL.revokeObjectURL(url);
//             document.body.removeChild(a);
//         })
//         .catch(error => console.error('Ошибка при экспорте объявлений:', error));
// });
