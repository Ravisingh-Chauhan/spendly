// Video modal functionality
const videoModal = document.getElementById('videoModal');
const videoFrame = document.getElementById('videoFrame');
const youtubeUrl = 'https://www.youtube.com/embed/dQw4w9WgXcQ';

function openVideoModal() {
    videoFrame.src = youtubeUrl;
    videoModal.classList.add('show');
}

function closeVideoModal() {
    videoModal.classList.remove('show');
    videoFrame.src = '';
}

videoModal.addEventListener('click', function(event) {
    if (event.target === videoModal) {
        closeVideoModal();
    }
});

document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && videoModal.classList.contains('show')) {
        closeVideoModal();
    }
});
