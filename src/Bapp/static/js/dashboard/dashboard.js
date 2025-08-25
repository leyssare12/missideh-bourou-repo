document.addEventListener('DOMContentLoaded', function() {
    // Toggle sidebar on mobile
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');

    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('active');
    });

    // Navigation between sections
    const navLinks = document.querySelectorAll('.sidebar-nav a');
    const contentSections = document.querySelectorAll('.content-section');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            // Remove active class from all links and sections
            navLinks.forEach(item => item.parentElement.classList.remove('active'));
            contentSections.forEach(section => section.classList.remove('active'));

            // Add active class to clicked link
            this.parentElement.classList.add('active');

            // Show corresponding content section
            const contentId = this.getAttribute('data-content');
            document.getElementById(contentId).classList.add('active');

            // Close sidebar on mobile after clicking a link
            if (window.innerWidth < 768) {
                sidebar.classList.remove('active');
            }
        });
    });

    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');

    logoutBtn.addEventListener('click', function() {
        // Here you would typically redirect to a logout page or handle logout logic
        alert('Déconnexion effectuée');
        // window.location.href = '/logout';
    });

    // Sample Chart.js implementation
    const ctx = document.getElementById('mainChart').getContext('2d');
    const mainChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
            datasets: [{
                label: 'Utilisateurs actifs',
                data: [120, 190, 170, 220, 250, 280, 310],
                backgroundColor: 'rgba(67, 97, 238, 0.2)',
                borderColor: 'rgba(67, 97, 238, 1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }, {
                label: 'Nouveaux utilisateurs',
                data: [50, 70, 90, 120, 150, 180, 200],
                backgroundColor: 'rgba(72, 149, 239, 0.2)',
                borderColor: 'rgba(72, 149, 239, 1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e) {
        if (window.innerWidth < 768 && !sidebar.contains(e.target) && e.target !== sidebarToggle) {
            sidebar.classList.remove('active');
        }
    });
});