/*!
 * Start Bootstrap - Creative v6.0.4 (https://startbootstrap.com/theme/creative)
 * Copyright 2013-2020 Start Bootstrap
 * Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-creative/blob/master/LICENSE)
 */
(function($) {
        // Start of use strict

        // Closes responsive menu when a scroll trigger link is clicked
        $('.js-scroll-trigger').click(function() {
                $('.navbar-collapse').collapse('hide');
        });

        // Activate scrollspy to add active class to navbar items on scroll
        $('body').scrollspy({
                target: '#mainNav',
                offset: 75,
        });

        // Collapse Navbar
        const navbarCollapse = function() {
                if ($('#mainNav').offset().top > 100) {
                        $('#mainNav').addClass('navbar-scrolled');
                } else {
                        $('#mainNav').removeClass('navbar-scrolled');
                }
        };
        // Collapse now if page is not at top
        navbarCollapse();
        // Collapse the navbar when page is scrolled
        $(window).scroll(navbarCollapse);

        // Magnific popup calls
        $('#portfolio').magnificPopup({
                delegate: 'a',
                type: 'image',
                tLoading: 'Loading image #%curr%...',
                mainClass: 'mfp-img-mobile',
                gallery: {
                        enabled: true,
                        navigateByImgClick: true,
                        preload: [0, 1],
                },
                image: {
                        tError: '<a href="%url%">The image #%curr%</a> could not be loaded.',
                },
        });
})(jQuery); // End of use strict

const TxtRotate = function(el, toRotate, period) {
        this.toRotate = toRotate;
        this.el = el;
        this.loopNum = 0;
        this.period = parseInt(period, 10) || 2000;
        this.txt = '';
        this.tick();
        this.isDeleting = false;
};

TxtRotate.prototype.tick = function() {
        const i = this.loopNum % this.toRotate.length;
        const fullTxt = this.toRotate[i];

        if (this.isDeleting) {
                this.txt = fullTxt.substring(0, this.txt.length - 1);
        } else {
                this.txt = fullTxt.substring(0, this.txt.length + 1);
        }

        this.el.innerHTML = `<span class="wrap">${this.txt}</span>`;

        const that = this;
        let delta = 300 - Math.random() * 100;

        if (this.isDeleting) {
                delta /= 2;
        }

        if (!this.isDeleting && this.txt === fullTxt) {
                delta = this.period;
                this.isDeleting = true;
        } else if (this.isDeleting && this.txt === '') {
                this.isDeleting = false;
                this.loopNum++;
                delta = 500;
        }

        setTimeout(function() {
                that.tick();
        }, delta);
};

window.onload = function() {
        const elements = document.getElementsByClassName('txt-rotate');
        for (let i = 0; i < elements.length; i++) {
                const toRotate = elements[i].getAttribute('data-rotate');
                const period = elements[i].getAttribute('data-period');
                if (toRotate) {
                        new TxtRotate(elements[i], JSON.parse(toRotate), period);
                }
        }
        // INJECT CSS
        const css = document.createElement('style');
        css.type = 'text/css';
        css.innerHTML = '.txt-rotate > .wrap { border-right: 0.08em solid #666 }';
        document.body.appendChild(css);
};
