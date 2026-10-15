// Auto Job — Interactive Frontend & GSAP Motion Engine

document.addEventListener('DOMContentLoaded', () => {
    // 1. GSAP Hero Entrance Animations
    if (typeof gsap !== 'undefined') {
        gsap.from('.gsap-hero', {
            opacity: 0,
            y: 28,
            duration: 0.9,
            stagger: 0.12,
            ease: 'power3.out'
        });

        // 2. 3D Tilt Parallax on Terminal Deck
        const terminalDeck = document.getElementById('terminal-deck');
        if (terminalDeck) {
            terminalDeck.addEventListener('mousemove', (e) => {
                const rect = terminalDeck.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;
                gsap.to(terminalDeck, {
                    rotationY: x * 0.04,
                    rotationX: -y * 0.04,
                    transformPerspective: 1000,
                    ease: 'power1.out',
                    duration: 0.4
                });
            });

            terminalDeck.addEventListener('mouseleave', () => {
                gsap.to(terminalDeck, {
                    rotationY: 0,
                    rotationX: 0,
                    ease: 'power2.out',
                    duration: 0.6
                });
            });
        }

        // 3. ScrollTrigger reveal for pipeline cards
        if (typeof ScrollTrigger !== 'undefined') {
            gsap.registerPlugin(ScrollTrigger);

            gsap.from('.pipeline-card', {
                scrollTrigger: {
                    trigger: '.pipeline-grid',
                    start: 'top 80%'
                },
                opacity: 0,
                y: 35,
                duration: 0.7,
                stagger: 0.12,
                ease: 'power2.out'
            });

            gsap.from('.byok-pill-box', {
                scrollTrigger: {
                    trigger: '.byok-grid',
                    start: 'top 82%'
                },
                opacity: 0,
                y: 25,
                duration: 0.6,
                stagger: 0.1,
                ease: 'power2.out'
            });
        }
    }

    // 4. Device Tab Switcher
    const tabButtons = document.querySelectorAll('.device-tab-btn');
    const tabSlides = document.querySelectorAll('.tab-slide');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-target');

            tabButtons.forEach(b => b.classList.remove('active'));
            tabSlides.forEach(s => s.classList.remove('active'));

            btn.classList.add('active');
            const activeSlide = document.getElementById(`pane-${target}`);
            if (activeSlide) {
                activeSlide.classList.add('active');
                if (typeof gsap !== 'undefined') {
                    gsap.fromTo(activeSlide, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.35, ease: 'power2.out' });
                }
            }
        });
    });

    // 5. Interactive Quota Calculator
    const slider = document.getElementById('jobs-slider');
    const jobsVal = document.getElementById('calc-jobs-val');
    const tokensVal = document.getElementById('calc-tokens');
    const pctVal = document.getElementById('calc-pct');

    if (slider) {
        const updateCalc = () => {
            const jobs = parseInt(slider.value, 10);
            jobsVal.textContent = `${jobs} Jobs`;

            // Approx 2,500 tokens per full screening analysis & auto-fill
            const tokens = jobs * 2500;
            tokensVal.textContent = `~${tokens.toLocaleString()} Tokens`;

            // Google provides 1,000,000 free tokens daily per Gmail account
            const pct = ((tokens / 1000000) * 100).toFixed(1);
            pctVal.textContent = `${pct}% of Daily Free Allowance (1M tokens)`;
        };

        slider.addEventListener('input', updateCalc);
        updateCalc();
    }

    // 6. FAQ Accordion Toggle
    const faqUnits = document.querySelectorAll('.faq-unit');
    faqUnits.forEach(unit => {
        const trigger = unit.querySelector('.faq-trigger');
        trigger.addEventListener('click', () => {
            const isOpen = unit.classList.contains('open');
            faqUnits.forEach(u => u.classList.remove('open'));
            if (!isOpen) {
                unit.classList.add('open');
            }
        });
    });

    // 7. Simulated Live Console Output (Strictly Generic Company Names)
    const consoleScreen = document.getElementById('console-screen');
    if (consoleScreen) {
        const genericLogs = [
            "[00:06.15] Job 3: Globex Systems — Distributed Systems Engineer",
            "↳ Detected ATS: Greenhouse Universal Form",
            "  ✓ Injected candidate profile & uploaded resume.pdf",
            "  ✓ Submission verified! Received HTTP 200 receipt",
            "[00:09.42] Job 4: CloudScale Data — Backend Engineer",
            "↳ Detected ATS: Lever Universal Application Adapter",
            "  ✓ Attached PDF resume & submitted candidate application",
            "★ Total verified applications updated in audit ledger"
        ];

        let logIdx = 0;
        setInterval(() => {
            if (logIdx < genericLogs.length) {
                const line = document.createElement('div');
                line.className = 'c-row c-green';
                line.textContent = genericLogs[logIdx];
                consoleScreen.appendChild(line);
                consoleScreen.scrollTop = consoleScreen.scrollHeight;
                logIdx++;
            }
        }, 4500);
    }
});

// Global snippet copy handler
function copySnippet(button) {
    const parent = button.parentElement;
    const codeTag = parent.querySelector('code');
    if (codeTag) {
        navigator.clipboard.writeText(codeTag.textContent.trim()).then(() => {
            const originalText = button.textContent;
            button.textContent = 'Copied!';
            button.style.backgroundColor = '#10B981';
            setTimeout(() => {
                button.textContent = originalText;
                button.style.backgroundColor = '';
            }, 2000);
        });
    }
}
