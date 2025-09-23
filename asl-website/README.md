# ASL Practice - Modern Fingerspelling Training

A sleek, minimalist web application for practicing American Sign Language (ASL) fingerspelling with enhanced features and modern design.

## Features

### Core Functionality
- **Interactive Fingerspelling Practice**: Visual letter-by-letter display with customizable speed
- **Real-time Feedback**: Instant validation with visual and color-coded responses
- **Score Tracking**: Monitor progress with persistent scoring system
- **Word Filtering**: Practice with words of specific lengths (3-6 letters or any length)

### Enhanced Features
- **Speed Control**: Four preset speeds (Slow, Medium, Fast, Expert) plus fine-tuning
- **Smart Word Selection**: Prevents repetition until all available words are used
- **Keyboard Shortcuts**: 
  - `N` - New word
  - `R` - Replay current word
  - `Space` - Replay or advance (context-sensitive)
- **Auto-advance**: Automatically moves to next word after correct answers
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices

### Technical Features
- **Offline Support**: Service worker enables offline functionality
- **Modern Architecture**: ES6+ JavaScript with class-based structure
- **Accessibility**: Proper focus management and keyboard navigation
- **Performance**: Optimized image loading and caching

## Design

### Visual Identity
- **Typography**: Inter font family with multiple weights (300-700)
- **Color Scheme**: 
  - Primary: Dark Navy Blue (#1e3a8a)
  - Background: Light Grey (#f8fafc)
  - Text: Black (#000000)
  - Accent: Success Green (#10b981) / Error Red (#ef4444)
- **Layout**: Clean, minimalist design with card-based components
- **Animations**: Subtle transitions and feedback states

### User Experience
- **Intuitive Controls**: Clear, accessible button design
- **Visual Hierarchy**: Proper spacing and typography scales
- **Feedback Systems**: Color-coded responses and clear messaging
- **Mobile-First**: Responsive design that works on all devices

## File Structure

```
asl-website/
├── index.html              # Main application page
├── sw.js                   # Service worker for offline support
├── assets/
│   ├── css/
│   │   └── style.css       # Modern CSS with custom properties
│   ├── js/
│   │   ├── app.js          # Main application logic
│   │   └── words.js        # Word database
│   └── images/
│       ├── [a-z].gif       # Individual letter images
│       ├── [a-z][a-z].gif  # Double letter images
│       ├── goodjob.png     # Success feedback image
│       ├── tryagain.png    # Error feedback image
│       └── blank.gif       # Placeholder image
└── README.md               # This documentation
```

## Usage

1. **Starting Practice**: Click "New Word" to begin
2. **Answering**: Type the word you see spelled out and press "Check" or Enter
3. **Speed Adjustment**: Use radio buttons or fine-tune controls to adjust playback speed
4. **Word Length**: Select maximum word length for targeted practice
5. **Navigation**: Use keyboard shortcuts for faster interaction

## Browser Support

- Modern browsers with ES6+ support
- Chrome 60+, Firefox 55+, Safari 12+, Edge 79+
- Progressive Web App features in supported browsers

## Development

The application uses vanilla JavaScript with modern features:
- ES6 Classes and modules
- Async/await patterns
- Service Workers
- CSS Custom Properties
- Flexbox and Grid layouts

## Copyright

© 2025 Tobias Schmidt Services LLC
