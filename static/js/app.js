document.addEventListener('DOMContentLoaded', function() {
    // Handle the launch button click
    const launchBtn = document.getElementById('launch-btn');
    if (launchBtn) {
        launchBtn.addEventListener('click', function() {
            window.location.href = '/launch';
        });
    }
    
    // Any additional client-side functionality can go here
});