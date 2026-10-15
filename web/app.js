// Auto Job Client-Side Script

document.addEventListener('DOMContentLoaded', () => {
    // 1. Device Tab Switcher
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const device = button.getAttribute('data-device');

            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanels.forEach(panel => panel.classList.remove('active'));

            button.classList.add('active');
            const targetPanel = document.getElementById(`panel-${device}`);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
        });
    });

    // 2. FAQ Accordion Toggle
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const toggleBtn = item.querySelector('.faq-toggle');
        toggleBtn.addEventListener('click', () => {
            const isOpen = item.classList.contains('open');
            // Close other items
            faqItems.forEach(i => i.classList.remove('open'));
            // Toggle current
            if (!isOpen) {
                item.classList.add('open');
            }
        });
    });

    // 3. Simulated Live Console Feed in Mockup
    const consoleStream = document.getElementById('console-stream');
    if (consoleStream) {
        const extraLogs = [
            "[03/52] Navigating: Insight Consultants (Greenhouse ATS)",
            "✓ Auto-populated contact details & attached resume.pdf",
            "✓ Submission complete! Status: 200 OK",
            "[04/52] Navigating: Weekday Full Stack (Direct ATS Bridge)",
            "★ Submitted successfully! Added to APPLICATIONS_REPORT.md"
        ];

        let logIndex = 0;
        setInterval(() => {
            if (logIndex < extraLogs.length) {
                const line = document.createElement('div');
                line.className = 'c-line c-success';
                line.textContent = extraLogs[logIndex];
                consoleStream.appendChild(line);
                consoleStream.scrollTop = consoleStream.scrollHeight;
                logIndex++;
            }
        }, 4000);
    }
});

// Global copy function for terminal commands
function copyCode(button) {
    const commandBox = button.parentElement.querySelector('code');
    if (commandBox) {
        navigator.clipboard.writeText(commandBox.textContent.trim()).then(() => {
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
