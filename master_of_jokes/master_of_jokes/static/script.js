document.addEventListener('DOMContentLoaded', function() {
    // Disable clicks on links with 'disabled' class
    document.querySelectorAll('a.disabled').forEach(function(element) {
        element.addEventListener('click', function(event) {
            event.preventDefault();
        });
    });

    // Title word count validation for joke creation
    const titleInput = document.getElementById('title');
    if (titleInput) {
        titleInput.addEventListener('input', function() {
            const wordCount = this.value.trim().split(/\s+/).length;
            if (wordCount > 10) {
                this.setCustomValidity('Title cannot be more than 10 words');
            } else {
                this.setCustomValidity('');
            }
        });
    }
});