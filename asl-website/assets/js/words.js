// Word list for ASL fingerspelling practice
const words = [
    "the", "be", "of", "and", "in", "to", "have", "it", "for", "that",
    "you", "he", "on", "with", "do", "at", "by", "not", "this", "but",
    "from", "they", "his", "she", "or", "which", "as", "we", "an", "say",
    "will", "would", "can", "if", "their", "go", "what", "there", "all", "get",
    "her", "make", "who", "out", "up", "time", "has", "look", "two", "more",
    "write", "see", "number", "no", "way", "could", "people", "my", "than", "first",
    "water", "been", "call", "its", "now", "find", "long", "down", "day", "did",
    "get", "come", "made", "may", "part", "over", "new", "sound", "take", "only",
    "little", "work", "know", "place", "year", "live", "me", "back", "give", "most",
    "very", "after", "thing", "our", "name", "good", "sentence", "man", "think", "say",
    "great", "where", "help", "through", "much", "before", "line", "right", "too", "mean",
    "old", "any", "same", "tell", "boy", "follow", "came", "want", "show", "also",
    "around", "farm", "three", "small", "set", "put", "end", "why", "again", "turn",
    "here", "off", "went", "old", "number", "great", "tell", "men", "say", "small",
    "every", "found", "still", "between", "name", "should", "home", "big", "give", "air",
    "line", "set", "own", "under", "read", "last", "never", "us", "left", "end",
    "along", "while", "might", "next", "sound", "below", "saw", "something", "thought", "both",
    "few", "those", "always", "show", "large", "often", "together", "asked", "house", "don't",
    "world", "going", "want", "school", "important", "until", "form", "food", "keep", "children",
    "feet", "land", "side", "without", "boy", "once", "animal", "life", "enough", "took",
    "sometimes", "four", "head", "above", "kind", "began", "almost", "live", "page", "got",
    "earth", "need", "far", "hand", "high", "year", "mother", "light", "country", "father",
    "let", "night", "picture", "being", "study", "second", "book", "carry", "science", "eat",
    "room", "friend", "began", "idea", "fish", "mountain", "north", "once", "base", "hear",
    "horse", "cut", "sure", "watch", "color", "face", "wood", "main", "enough", "plain",
    "girl", "usual", "young", "ready", "above", "ever", "red", "list", "though", "feel",
    "talk", "bird", "soon", "body", "dog", "family", "direct", "pose", "leave", "song",
    "measure", "door", "product", "black", "short", "numeral", "class", "wind", "question", "happen",
    "complete", "ship", "area", "half", "rock", "order", "fire", "south", "problem", "piece",
    "told", "knew", "pass", "since", "top", "whole", "king", "space", "heard", "best",
    "hour", "better", "during", "hundred", "five", "remember", "step", "early", "hold", "west",
    "ground", "interest", "reach", "fast", "verb", "sing", "listen", "six", "table", "travel",
    "less", "morning", "ten", "simple", "several", "vowel", "toward", "war", "lay", "against",
    "pattern", "slow", "center", "love", "person", "money", "serve", "appear", "road", "map",
    "rain", "rule", "govern", "pull", "cold", "notice", "voice", "unit", "power", "town",
    "fine", "certain", "fly", "fall", "lead", "cry", "dark", "machine", "note", "wait",
    "plan", "figure", "star", "box", "noun", "field", "rest", "correct", "able", "pound",
    "done", "beauty", "drive", "stood", "contain", "front", "teach", "week", "final", "gave",
    "green", "oh", "quick", "develop", "ocean", "warm", "free", "minute", "strong", "special",
    "mind", "behind", "clear", "tail", "produce", "fact", "street", "inch", "multiply", "nothing",
    "course", "stay", "wheel", "full", "force", "blue", "object", "decide", "surface", "deep",
    "moon", "island", "foot", "system", "busy", "test", "record", "boat", "common", "gold",
    "possible", "plane", "stead", "dry", "wonder", "laugh", "thousands", "ago", "ran", "check",
    "game", "shape", "equate", "hot", "miss", "brought", "heat", "snow", "tire", "bring",
    "yes", "distant", "fill", "east", "paint", "language", "among"
];

// Sort words by length for efficient filtering
words.sort((a, b) => a.length - b.length);

// Export for use in main application
if (typeof module !== 'undefined' && module.exports) {
    module.exports = words;
}
