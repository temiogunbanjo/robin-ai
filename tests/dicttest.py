from storage.datasets import word_index

words = {
    k: (v + 3) for k, v in word_index.items()
}
words["<PAD>"] = 0
words["<START>"] = 1
words["<UNK>"] = 2
words["<UNUSED>"] = 3

print(words.items())

# Reverse key/value pair
text = [1, 6, 5, 4, 1, 25]

reverse = dict([(v, k) for (k, v) in words.items()])
print([reverse.get(i, "0") for i in text])
