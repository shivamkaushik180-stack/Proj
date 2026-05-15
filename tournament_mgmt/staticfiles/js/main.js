/* ═══════════════════════════════════════════════════════════
   OGTRMS - Main JavaScript (Final Optimized Version)
   Online Gaming Tournament Registration & Management System
═══════════════════════════════════════════════════════════ */

'use strict';

/* ==========================================================
   UTILITY FUNCTIONS
========================================================== */
function debounce(fn, delay = 500) {
    let timer;
    return function () {
        clearTimeout(timer);
        const args = arguments;
        const context = this;

        timer = setTimeout(() => {
            fn.apply(context, args);
        }, delay);
    };
}

/* ==========================================================
   DOM READY
========================================================== */
document.addEventListener("DOMContentLoaded", function () {

    /* ======================================================
       PAGE LOADER
    ====================================================== */
    window.addEventListener("load", function () {
        const loader = document.querySelector(".loading-overlay");

        if (loader) {
            setTimeout(() => {
                loader.style.opacity = "0";

                setTimeout(() => {
                    loader.remove();
                }, 500);

            }, 300);
        }
    });

    /* ======================================================
       NAVBAR SCROLL EFFECT
    ====================================================== */
    const navbar = document.getElementById("mainNav");

    if (navbar) {
        window.addEventListener("scroll", function () {
            navbar.classList.toggle("scrolled", window.scrollY > 50);
        });
    }

    /* ======================================================
       ANIMATE ON SCROLL
    ====================================================== */
    if ('IntersectionObserver' in window) {

        const animationObserver = new IntersectionObserver((entries) => {

            entries.forEach(entry => {

                if (entry.isIntersecting) {

                    const animation =
                        entry.target.dataset.aos ||
                        "animate__fadeInUp";

                    entry.target.classList.add(
                        "animate__animated",
                        animation
                    );

                    entry.target.style.opacity = "1";

                    animationObserver.unobserve(entry.target);
                }
            });

        }, {
            threshold: 0.1
        });

        document.querySelectorAll("[data-aos]").forEach(el => {
            el.style.opacity = "0";
            animationObserver.observe(el);
        });
    }

    /* ======================================================
       COUNTDOWN TIMER
    ====================================================== */
    function initCountdown(id, targetDate) {

        const box = document.getElementById(id);
        if (!box) return;

        const target = new Date(targetDate).getTime();

        const days = box.querySelector(".days");
        const hours = box.querySelector(".hours");
        const mins = box.querySelector(".mins");
        const secs = box.querySelector(".secs");

        function update() {

            const now = new Date().getTime();
            const diff = target - now;

            if (diff <= 0) {
                box.innerHTML =
                    '<span class="text-success fw-bold">Tournament Started!</span>';
                return;
            }

            const d = Math.floor(diff / (1000 * 60 * 60 * 24));
            const h = Math.floor((diff / (1000 * 60 * 60)) % 24);
            const m = Math.floor((diff / (1000 * 60)) % 60);
            const s = Math.floor((diff / 1000) % 60);

            if (days) days.textContent = String(d).padStart(2, "0");
            if (hours) hours.textContent = String(h).padStart(2, "0");
            if (mins) mins.textContent = String(m).padStart(2, "0");
            if (secs) secs.textContent = String(s).padStart(2, "0");
        }

        update();
        setInterval(update, 1000);
    }

    document.querySelectorAll("[data-countdown]").forEach(el => {
        initCountdown(el.id, el.dataset.countdown);
    });

    /* ======================================================
       COUNTER ANIMATION
    ====================================================== */
    if ('IntersectionObserver' in window) {

        const counterObserver = new IntersectionObserver((entries) => {

            entries.forEach(entry => {

                if (entry.isIntersecting) {

                    const el = entry.target;

                    const target = parseInt(
                        el.dataset.count ||
                        el.textContent.replace(/,/g, "")
                    );

                    if (!isNaN(target)) {

                        let start = 0;
                        const duration = 1500;
                        const step = Math.ceil(target / 60);

                        const timer = setInterval(() => {

                            start += step;

                            if (start >= target) {
                                start = target;
                                clearInterval(timer);
                            }

                            el.textContent =
                                start.toLocaleString();

                        }, duration / 60);
                    }

                    counterObserver.unobserve(el);
                }
            });

        }, {
            threshold: 0.5
        });

        document.querySelectorAll("[data-count]").forEach(el => {
            counterObserver.observe(el);
        });
    }

    /* ======================================================
       SEARCH AUTO SUBMIT
    ====================================================== */
    const searchInput =
        document.getElementById("tournamentSearch");

    if (searchInput) {
        searchInput.addEventListener(
            "input",
            debounce(function () {
                const form = this.closest("form");
                if (form) form.submit();
            }, 700)
        );
    }

    /* ======================================================
       FILE IMAGE PREVIEW
    ====================================================== */
    document.querySelectorAll('input[type="file"]').forEach(input => {

        input.addEventListener("change", function () {

            const file = this.files[0];
            if (!file) return;

            const previewId = this.dataset.preview;
            if (!previewId) return;

            const img =
                document.getElementById(previewId);

            if (!img) return;

            const reader = new FileReader();

            reader.onload = function (e) {
                img.src = e.target.result;
                img.style.display = "block";
            };

            reader.readAsDataURL(file);
        });
    });

    /* ======================================================
       ALERT AUTO CLOSE
    ====================================================== */
    setTimeout(() => {

        document.querySelectorAll(".alert").forEach(el => {

            if (typeof bootstrap !== "undefined") {

                const alert =
                    bootstrap.Alert.getOrCreateInstance(el);

                setTimeout(() => {
                    try {
                        alert.close();
                    } catch (e) { }
                }, 5000);
            }
        });

    }, 100);

    /* ======================================================
       BOOTSTRAP TOOLTIP
    ====================================================== */
    if (typeof bootstrap !== "undefined") {

        document.querySelectorAll(
            '[data-bs-toggle="tooltip"]'
        ).forEach(el => {
            new bootstrap.Tooltip(el);
        });
    }

    /* ======================================================
       SMOOTH SCROLL
    ====================================================== */
    document.querySelectorAll('a[href^="#"]').forEach(link => {

        link.addEventListener("click", function (e) {

            const target =
                document.querySelector(
                    this.getAttribute("href")
                );

            if (target) {
                e.preventDefault();

                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });
            }
        });
    });

    /* ======================================================
       COPY TO CLIPBOARD
    ====================================================== */
    document.querySelectorAll("[data-copy]").forEach(btn => {

        btn.addEventListener("click", function () {

            const text = this.dataset.copy;

            navigator.clipboard.writeText(text).then(() => {

                const old = this.innerHTML;

                this.innerHTML =
                    '<i class="fas fa-check"></i> Copied';

                setTimeout(() => {
                    this.innerHTML = old;
                }, 2000);

            }).catch(() => { });
        });
    });

    /* ======================================================
       OTP AUTO FOCUS
    ====================================================== */
    const otpInput =
        document.querySelector(".otp-input");

    if (otpInput) {
        otpInput.addEventListener("input", function () {

            if (this.value.length === 6) {

                const btn =
                    this.closest("form")
                    ?.querySelector(
                        'button[type="submit"]'
                    );

                if (btn) btn.focus();
            }
        });
    }

    /* ======================================================
       PARTICLES
    ====================================================== */
    function createParticles(box, count = 15) {

        if (!box) return;

        for (let i = 0; i < count; i++) {

            const p = document.createElement("div");

            p.className = "particle";

            p.style.left =
                Math.random() * 100 + "%";

            p.style.animationDuration =
                (4 + Math.random() * 5) + "s";

            p.style.animationDelay =
                (Math.random() * 4) + "s";

            box.appendChild(p);
        }
    }

    document.querySelectorAll(".particles").forEach(el => {
        createParticles(el, 18);
    });

    /* ======================================================
       LIVE SLOT UPDATE
    ====================================================== */
    function updateSlots() {

        document.querySelectorAll(
            "[data-tournament-id]"
        ).forEach(card => {

            const id =
                card.dataset.tournamentId;

            fetch(`/api/tournament/${id}/slots/`)
                .then(res => res.json())
                .then(data => {

                    const txt =
                        card.querySelector(".slots-left");

                    const bar =
                        card.querySelector(".slot-fill");

                    if (txt)
                        txt.textContent =
                        data.slots_left;

                    if (bar)
                        bar.style.width =
                        data.fill_percentage + "%";

                })
                .catch(() => { });
        });
    }

    if (
        document.querySelectorAll(
            "[data-tournament-id]"
        ).length
    ) {
        setInterval(updateSlots, 30000);
    }

    /* ======================================================
       SOUND MANAGER (FINAL FIXED)
    ====================================================== */
    const sounds = {
        click: new Audio("/static/sounds/click.mp3"),
        hover: new Audio("/static/sounds/hover.mp3"),
        success: new Audio("/static/sounds/success.mp3"),
        error: new Audio("/static/sounds/error.mp3"),
        notification: new Audio("/static/sounds/notification.mp3"),
        button: new Audio("/static/sounds/button.mp3")
    };

    Object.values(sounds).forEach(sound => {
        sound.volume = 0.7;
        sound.preload = "auto";
    });

    function play(name) {

        const sound = sounds[name];
        if (!sound) return;

        sound.pause();
        sound.currentTime = 0;

        sound.play().catch(() => { });
    }

    /* Unlock audio first user click */
    document.body.addEventListener("click", function unlock() {
        play("click");
    }, { once: true });

    /* Click sounds */
    document.addEventListener("click", function (e) {

        if (e.target.closest("button,.btn")) {
            play("button");
        }
        else if (e.target.closest("a")) {
            play("click");
        }
    });

    /* Hover with delay anti-spam */
    let hoverReady = true;

    document.addEventListener("mouseover", function (e) {

        if (
            hoverReady &&
            e.target.closest("button,.btn,a")
        ) {
            hoverReady = false;

            play("hover");

            setTimeout(() => {
                hoverReady = true;
            }, 150);
        }
    });

    /* Global manual functions */
    window.playSuccess = function () {
        play("success");
    };

    window.playError = function () {
        play("error");
    };

    window.playNotification = function () {
        play("notification");
    };

    /* ======================================================
       CONSOLE BRANDING
    ====================================================== */
    console.log(
        "%cOGTRMS v2.0",
        "color:#00f5ff;font-size:20px;font-weight:bold;"
    );

});