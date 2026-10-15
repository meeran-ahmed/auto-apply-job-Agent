// OmniSwarm Client-Side Interactivity

document.addEventListener('DOMContentLoaded', () => {
    // 1. Navbar scroll effect
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 40) {
            navbar.style.borderBottomColor = 'rgba(0, 240, 255, 0.2)';
            navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.5)';
        } else {
            navbar.style.borderBottomColor = 'rgba(255, 255, 255, 0.08)';
            navbar.style.boxShadow = 'none';
        }
    });

    // 2. Terminal Live Stream Simulation
    const terminalOutput = document.getElementById('terminal-output');
    if (terminalOutput) {
        const extraLogs = [
            "[3/52] Navigating: Insight Consultants -> Detected ATS: Greenhouse Universal",
            "  ✓ Auto-populated candidate form fields & attached resume.pdf",
            "  ✓ Form submitted! Response code: 200 OK",
            "[4/52] Navigating: Weekday Full Stack -> Auto-submitted via Direct ATS bridge!",
            "✨ Live Swarm Efficiency: 94.2% Success Rate • Safe delay pacing active"
        ];

        let index = 0;
        setInterval(() => {
            if (index < extraLogs.length) {
                const p = document.createElement('p');
                p.className = 'term-line term-green';
                p.textContent = extraLogs[index];
                terminalOutput.appendChild(p);
                index++;
            }
        }, 3500);
    }
});
