#!/usr/bin/env python3

DICT_FILE = "/usr/share/dict/words"

from collections import Counter, defaultdict
from enum import Enum
from string import ascii_lowercase
import sys

class GuessState(Enum):
    UNKNOWN = "_"
    INCORRECT = "x"
    MISPLACED = "?"
    CORRECT = "+"

class SkipWordError(Exception):
    pass

def input_guess(expect_len=None):
    while True:
        text_input = input("Result [_x?+]: ").strip()
        if not text_input:
            raise SkipWordError()
        if expect_len is not None and len(text_input) != expect_len:
            print(f"Expected {expect_len} symbols")
        else:
            break
    return [GuessState(i) for i in text_input]

def read_dictionary(word_length):
    with open(DICT_FILE) as dict_fd:
        return set(word for word in
                   (line.strip().lower() for line in dict_fd)
                   if len(word) == word_length)

def letter_word_counts(words):
    word = words.pop()
    counts = [defaultdict(int) for i in range(len(word))]
    words.add(word)
    for word in words:
        for position, letter in enumerate(word):
            counts[position][letter] += 1
    return counts

def find_suggestions(words, num_suggestions):
    counts = letter_word_counts(words)
    scores = []
    for word in words:
        scores.append((sum(
                counts[position][letter]
                for position, letter in enumerate(word)),
            word))
    return sorted(scores, reverse=True)[:num_suggestions]

def find_min_max_letter_repeats(words):
    min_repeats = {letter: 999 for letter in ascii_lowercase}
    max_repeats = {letter: 0 for letter in ascii_lowercase}
    for word in words:
        word_count = Counter(word)
        for letter in ascii_lowercase:
            min_repeats[letter] = min(min_repeats[letter], word_count[letter])
            max_repeats[letter] = max(max_repeats[letter], word_count[letter])
    return min_repeats, max_repeats

class WordleSolver:

    def __init__(self, word_len):
        self.word_len = word_len
        self.words = read_dictionary(word_len)
        min_repeats, max_repeats = find_min_max_letter_repeats(self.words)
        self.correct_letters = [None] * word_len
        self.misplaced_letters = defaultdict(set)
        self.letter_counts = {letter: [min_repeats[letter], max_repeats[letter]]
                              for letter in ascii_lowercase}

    def process_feedback(self, suggestion, feedback):
        correct_letter_counts = defaultdict(int)
        incorrect_letter_counts = defaultdict(int)
        for offset, (letter, result) in enumerate(zip(suggestion, feedback)):
            if result == GuessState.INCORRECT:
                incorrect_letter_counts[letter] += 1
                self.misplaced_letters[letter].add(offset)
            if result == GuessState.MISPLACED:
                correct_letter_counts[letter] += 1
                self.misplaced_letters[letter].add(offset)
            elif result == GuessState.CORRECT:
                correct_letter_counts[letter] += 1
                self.correct_letters[offset] = letter
        for letter, count in correct_letter_counts.items():
            self.letter_counts[letter][0] = max(count, self.letter_counts[letter][0])
        suggestion_counts = Counter(suggestion)
        for letter, count in incorrect_letter_counts.items():
            max_count = suggestion_counts[letter] - count
            self.letter_counts[letter][1] = min(max_count, self.letter_counts[letter][1])

    def filter_words(self):
        new_words = set()
        for word in self.words:
            if any(letter is not None and letter != word[offset]
                for offset, letter in enumerate(self.correct_letters)):
                continue
            if any(offset in self.misplaced_letters[letter]
                for offset, letter in enumerate(word)):
                continue
            word_letter_counts = Counter(word)
            if any(not (self.letter_counts[letter][0] <= count <= self.letter_counts[letter][1])
                   for letter, count in word_letter_counts.items()):
                continue
            if any(not (min_count <= word_letter_counts[letter] <= max_count)
                for letter, (min_count, max_count) in self.letter_counts.items()):
                continue
            new_words.add(word)
        self.words = new_words

    def run_until_solved(self):
        while len(self.words) > 1:
            suggestions = find_suggestions(self.words, 10)
            feedback = None
            for suggestion in (i[1] for i in suggestions):
                print(f"Suggestion: {suggestion}")
                try:
                    feedback = input_guess(self.word_len)
                    break
                except SkipWordError:
                    pass
            if feedback is None:
                raise Exception("No suggestions accepted")
            self.process_feedback(suggestion,
                                  feedback)
            self.filter_words()
            min_repeats, max_repeats = find_min_max_letter_repeats(self.words)
            self.letter_counts = {letter: [max(min_count, min_repeats[letter]),
                                           min(max_count, max_repeats[letter])]
                                  for letter, (min_count, max_count) in self.letter_counts.items()}
        if len(self.words) == 1:
            return self.words.pop()
        return None

def main():
    print("Enter initial feedback with all '_' to set length")
    solver = WordleSolver(len(input_guess()))
    print("Remaining feedback: x = wrong letter, ? = right letter, wrong place, + = right letter")
    print("If the suggestion isn't accepted as a word, just hit enter to see next suggestion")
    solution = solver.run_until_solved()
    if solution is None:
        print("No solution found")
        return 1
    else:
        print(f"Solution: {solution}")
        return 0

if __name__ == "__main__":
    sys.exit(main())
