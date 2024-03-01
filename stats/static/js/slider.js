document.addEventListener('DOMContentLoaded', () => {
    let mySwiper = new Swiper('.slider-block', {
        slidesPerView: 'auto',
        mousewheel: {
            sensitivity: 1,
        },
        spaceBetween: 20,
    });

    let navSwiper = new Swiper('.slider-nav', {
        direction: 'vertical',
        slidesPerView: 6,
        freeMode: true,
        scrollbar: {
            el: '.swiper-scrollbar',
            draggable: true,
        },
        mousewheel: {
            sensitivity: 1,
        },
    });

    const sliderNavItems = document.querySelectorAll('.slider__item');

    sliderNavItems.forEach((el, index) => {
        el.addEventListener('click', () => {
            mySwiper.slideTo(index);
        });
    });
});

