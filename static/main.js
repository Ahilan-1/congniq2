document.addEventListener('DOMContentLoaded', function() {
    const quickAnswerElement = document.querySelector('.quick-answer');
    if (quickAnswerElement) {
        const text = quickAnswerElement.innerHTML;
        quickAnswerElement.innerHTML = '';
        let i = 0;
        const typingSpeed = 20; // Faster typing speed

        function typeWriter() {
            if (i < text.length) {
                const char = text.charAt(i);
                if (char === '<') {
                    const endIdx = text.indexOf('>', i);
                    quickAnswerElement.innerHTML += text.substring(i, endIdx + 1);
                    i = endIdx + 1;
                } else {
                    quickAnswerElement.innerHTML += char;
                    i++;
                }
                setTimeout(typeWriter, typingSpeed);
            }
        }

        typeWriter();
    }
});

function showLoadingSpinner() {
    const loader = document.createElement('div');
    loader.className = 'loader';
    document.body.appendChild(loader);
}

function showLoadingScreen() {
    document.getElementById('loading-screen').style.display = 'block';
}

// You can use this function to hide the loading screen after results are fetched
function hideLoadingScreen() {
    document.getElementById('loading-screen').style.display = 'none';
}

function hideLoadingSpinner() {
    const loader = document.querySelector('.loader');
    if (loader) {
        loader.remove();
    }
}

document.querySelector('form').addEventListener('submit', function() {
    showLoadingSpinner();
});
