import sys
import youtokentome as yttm

from pathlib import Path


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print('Usage: python build_vocab.py path_to_texts vocab_size vocab_coverage path_to_bert_vocab')
        exit(1)
    filepath = Path(sys.argv[1])  # path to tokenized texts
    vocab_size = int(sys.argv[2])  # size of new vocab (without special tokens)
    coverage = float(sys.argv[3])  # vocab coverage
    bert_vocab_file = Path(sys.argv[4])  # original bert vocab to take special tokens

    new_vocab_file = filepath.parent / f'vocab_{vocab_size}_{coverage}.txt'

    print(f'training vocab for: {filepath}')

    # train bpe vocab
    yttm_model_file = filepath.parent / 'yttm.model'
    yttm.BPE.train(data=str(filepath), vocab_size=vocab_size, model=str(yttm_model_file), coverage=coverage)

    bpe = yttm.BPE(model=str(yttm_model_file))

    print('building new vocab...')

    # make subtokens in bert notation, first five tokens are special tokens from yttm
    subtokens = bpe.vocab()[5:]

    characters = [s for s in subtokens if len(s) == 1]
    new_subtokens = []
    # take all characters
    new_subtokens += characters
    # take all chars as inner
    new_subtokens += [f'##{c}' for c in characters]
    # convert all > 2 char tokens from bpe to bert notation
    # if len > 2 and _ in s -- take s[1:]
    # if len > 1 and _ not in s -- take ##s
    new_subtokens += [s[1:] if '▁' in s else f'##{s}' for s in subtokens
                      if (len(s) > 1 and '▁' not in s) or (len(s) > 2 and '▁' in s)]

    # add special tokens from original bert vocab
    original_tokens = []
    with bert_vocab_file.open('r', encoding='utf8') as fin:
        for line in fin:
            if '[' in line and ']' in line:
                original_tokens += [line.strip()]
            else:
                break

    print(f'writing vocab to: {new_vocab_file}')
    # write new vocab
    with (new_vocab_file).open('w', encoding='utf8') as fout:
        for el in original_tokens + new_subtokens:
            fout.write(el + '\n')

    print('finished')
