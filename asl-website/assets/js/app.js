class ASLPractice {
    constructor() {
        this.currentWord = '';
        this.currentIndex = 0;
        this.speed = 800;
        this.maxLength = 99;
        this.maxAttempts = 3;
        this.currentAttempts = 0;
        this.mode = 'words';
        this.customWords = [];
        this.score = 0;
        this.usedWords = new Set();
        this.isPlaying = false;
        this.timeoutId = null;
        this.alphabet = 'abcdefghijklmnopqrstuvwxyz'.split('');
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.focusInput();
    }

    bindEvents() {
        document.getElementById('newWordBtn').addEventListener('click', () => this.newWord());
        document.getElementById('replayBtn').addEventListener('click', () => this.replayWord());
        
        document.getElementById('answerForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.checkAnswer();
        });

        document.querySelectorAll('input[name="speed"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.speed = parseInt(e.target.value);
            });
        });

        document.querySelectorAll('input[name="length"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.maxLength = parseInt(e.target.value);
                this.usedWords.clear();
            });
        });

        document.querySelectorAll('input[name="attempts"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.maxAttempts = parseInt(e.target.value);
            });
        });

        document.querySelectorAll('input[name="mode"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.mode = e.target.value;
                this.usedWords.clear();
                this.toggleCustomSection();
            });
        });

        document.getElementById('customWords').addEventListener('input', (e) => {
            this.extractWords(e.target.value);
        });

        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            
            if (e.key.toLowerCase() === 'n') {
                e.preventDefault();
                this.newWord();
            } else if (e.key.toLowerCase() === 'r') {
                e.preventDefault();
                this.replayWord();
            }
        });
    }

    extractWords(text) {
        // Smart word extraction - removes formatting, numbers, punctuation
        const words = text
            .toLowerCase()
            .replace(/[^\w\s]/g, ' ') // Replace punctuation with spaces
            .replace(/\d+/g, ' ') // Remove numbers
            .split(/\s+/) // Split on whitespace
            .filter(word => word.length > 1 && /^[a-z]+$/.test(word)) // Only letters, min 2 chars
            .filter((word, index, arr) => arr.indexOf(word) === index); // Remove duplicates
        
        this.customWords = words;
    }

    toggleCustomSection() {
        const section = document.getElementById('customSection');
        section.style.display = this.mode === 'custom' ? 'flex' : 'none';
    }

    focusInput() {
        document.getElementById('answerInput').focus();
    }

    getWordList() {
        switch (this.mode) {
            case 'alphabet':
                return this.alphabet;
            case 'custom':
                return this.customWords.length > 0 ? this.customWords : ['hello'];
            default:
                return words.filter(word => word.length <= this.maxLength);
        }
    }

    getRandomWord() {
        const availableWords = this.getWordList();
        
        if (this.usedWords.size >= availableWords.length) {
            this.usedWords.clear();
        }

        let word;
        do {
            word = availableWords[Math.floor(Math.random() * availableWords.length)];
        } while (this.usedWords.has(word) && this.usedWords.size < availableWords.length);

        this.usedWords.add(word);
        return word;
    }

    newWord() {
        this.stopPlayback();
        this.currentWord = this.getRandomWord();
        this.currentIndex = 0;
        this.currentAttempts = 0;
        
        const input = document.getElementById('answerInput');
        input.value = '';
        input.className = '';
        this.focusInput();
        
        this.playWord();
    }

    replayWord() {
        if (!this.currentWord) {
            this.newWord();
            return;
        }
        
        this.stopPlayback();
        this.currentIndex = 0;
        
        const input = document.getElementById('answerInput');
        input.className = '';
        this.focusInput();
        
        this.playWord();
    }

    stopPlayback() {
        this.isPlaying = false;
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
        }
    }

    playWord() {
        this.isPlaying = true;
        this.displayLetter();
    }

    displayLetter() {
        if (!this.isPlaying) return;

        const display = document.getElementById('letterDisplay');
        
        if (this.currentIndex >= this.currentWord.length) {
            display.innerHTML = '<div class="placeholder">Word complete</div>';
            this.isPlaying = false;
            return;
        }

        const letter = this.currentWord.charAt(this.currentIndex);
        
        const img = document.createElement('img');
        img.src = `assets/images/${letter}_converted.png`;
        img.alt = `ASL letter ${letter}`;
        
        img.onerror = () => {
            img.src = `assets/images/${letter}.gif`;
            img.onerror = () => {
                display.innerHTML = `<div class="placeholder" style="font-size: 48px; font-weight: 700;">${letter.toUpperCase()}</div>`;
            };
        };
        
        display.innerHTML = '';
        display.appendChild(img);
        
        this.currentIndex++;
        this.timeoutId = setTimeout(() => this.displayLetter(), this.speed);
    }

    checkAnswer() {
        const input = document.getElementById('answerInput');
        const userAnswer = input.value.toLowerCase().trim();
        const display = document.getElementById('letterDisplay');

        this.currentAttempts++;

        if (userAnswer === this.currentWord.toLowerCase()) {
            this.score++;
            document.getElementById('scoreValue').textContent = this.score;
            
            display.className = 'letter-display feedback-success';
            display.innerHTML = '<div>✓ Correct!</div>';
            input.className = 'correct';
            
            setTimeout(() => {
                display.className = 'letter-display';
                this.newWord();
            }, 1500);
            
        } else if (this.currentAttempts >= this.maxAttempts) {
            // Max attempts reached - show answer
            display.className = 'letter-display feedback-error';
            display.innerHTML = `<div>Answer: "${this.currentWord}"</div>`;
            input.className = 'incorrect';
            
            setTimeout(() => {
                display.className = 'letter-display';
                this.newWord();
            }, 2500);
            
        } else {
            // Still have attempts left
            display.className = 'letter-display feedback-error';
            display.innerHTML = `<div>✗ Try Again (${this.currentAttempts}/${this.maxAttempts})</div>`;
            input.className = 'incorrect';
            
            setTimeout(() => {
                display.className = 'letter-display';
                input.className = '';
                input.select();
            }, 1200);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ASLPractice();
});
