// Auto Job — Minimal Client-Side Interactivity

document.addEventListener('DOMContentLoaded', () => {
    // 1. Segmented Control Switcher
    const segmentButtons = document.querySelectorAll('.segment-btn');
    const platformPanes = document.querySelectorAll('.platform-pane');

    segmentButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-tab');

            segmentButtons.forEach(b => b.classList.remove('active'));
            platformPanes.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const activePane = document.getElementById(`pane-${target}`);
            if (activePane) {
                activePane.classList.add('active');
            }
        });
    });

    // 2. FAQ Accordion
    const accItems = document.querySelectorAll('.acc-item');
    accItems.forEach(item => {
        const trigger = item.querySelector('.acc-trigger');
        trigger.addEventListener('click', () => {
            const isOpen = item.classList.contains('open');
            accItems.forEach(i => i.classList.remove('open'));
            if (!isOpen) {
                item.classList.add('open');
            }
        });
    });

    // 3. Simulated Terminal Log (Strictly Generic Company Targets)
    const terminalScreen = document.getElementById('terminal-screen');
    if (terminalScreen) {
        const sampleLogs = [
            "[03/50] Navigating to target: Globex Data — Distributed Systems Engineer",
            "↳ ATS identified: Lever Universal Application Form",
            "✓ Attached candidate credentials & uploaded PDF resume",
            "✓ Submission complete! Status 200 OK",
            "[04/50] Navigating to target: CloudScale Infrastructure — Python Backend Engineer",
            "✓ Application submitted successfully via Direct ATS adapter"
        ];

        let index = 0;
        setInterval(() => {
            if (index < sampleLogs.length) {
                const row = document.createElement('div');
                row.className = 'log-row log-success';
                row.textContent = sampleLogs[index];
                terminalScreen.appendChild(row);
                terminalScreen.scrollTop = terminalScreen.scrollHeight;
                index++;
            }
        }, 5000);
    }
});

// Copy CLI command helper
function copyCli(button) {
    const parent = button.parentElement;
    const codeTag = parent.querySelector('code');
    if (codeTag) {
        navigator.clipboard.writeText(codeTag.textContent.trim()).then(() => {
            const prevText = button.textContent;
            button.textContent = 'Copied';
            setTimeout(() => {
                button.textContent = prevText;
            }, 2000);
        });
    }
}
