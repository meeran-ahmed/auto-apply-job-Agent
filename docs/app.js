// Auto Job — Glassmorphic Frontend & Tab Switcher

document.addEventListener('DOMContentLoaded', () => {
    // 1. Multi-Platform Tab Switcher
    const platformTabs = document.querySelectorAll('.plat-tab');
    const platformPanes = document.querySelectorAll('.plat-pane');

    platformTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.getAttribute('data-tab');

            platformTabs.forEach(t => t.classList.remove('active'));
            platformPanes.forEach(p => p.classList.remove('active'));

            tab.classList.add('active');
            const targetPane = document.getElementById(`pane-${target}`);
            if (targetPane) {
                targetPane.classList.add('active');
            }
        });
    });

    // 2. FAQ Accordion Collapsible
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const header = item.querySelector('.faq-header');
        if (header) {
            header.addEventListener('click', () => {
                const isOpen = item.classList.contains('open');
                faqItems.forEach(i => i.classList.remove('open'));
                if (!isOpen) {
                    item.classList.add('open');
                }
            });
        }
    });
});

// Copy snippet button helper
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
