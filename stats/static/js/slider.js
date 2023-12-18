document.addEventListener('DOMContentLoaded', () => {
    let mySwiper = new Swiper('.slider-block', {
        slidesPerView: 1,
        mousewheel: {
            sensitivity: 1,
        },
    })
    const maxItems = 5;
    const sliderNavItems = document.querySelectorAll('.slider-nav__item');
    const sliderNav = document.querySelector('.slider-nav');

    sliderNavItems.forEach((el, index) => {
        el.setAttribute('data-index', index);

        el.addEventListener('click', (e) => {
            const index = parseInt(e.currentTarget.dataset.index);
            console.log(index)
            mySwiper.slideTo(index);
        });
    });

    //    const showMore = () => {
    //        let childenLength = sliderNav.children.length;
    //        console.log(childenLength)
    //        if (childenLength > maxItems) {
    //            document.querySelectorAll(`.slider-nav__item:nth-child(n+${maxItems + 1})`)
    //                .forEach(el => {el.style.display = 'none';});
    //        }
    //
    //    };
    //
    //    showMore();
    $(document).ready(function(){
        $('.slider-nav').slick({
            slidesToShow: 5,
            vertical: true,
        });
    });
});
