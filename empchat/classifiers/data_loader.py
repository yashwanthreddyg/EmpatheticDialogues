from tqdm import tqdm
from typing import List, Dict
from torch.utils.data import Dataset
import collections
import re

from utils import UNK
from utils import build_label_idx, check_all_labels_in_dict, check_all_obj_is_None
from instance import Instance

Feature = collections.namedtuple('Feature',
                                 'words seq_len label')
Feature.__new__.__defaults__ = (None,) * 6


class EmotionDataset(Dataset):
    def __init__(self, file: str,
                 is_train: bool,
                 tokenizer,
                 replace_digits=False,
                 label2idx: Dict[str, int] = None):
        """
        Read the dataset into Instance
        """
        # read all the instances. sentences and labels
        self.tokenizer = tokenizer
        insts = self.read_txt(file, replace_digits)
        self.insts = insts
        if is_train:
            print(f"[Data Info] Using the training set to build label index")
            assert label2idx is None
            # build label to index mapping. e.g., joy -> 0, fun -> 1
            idx2labels, label2idx = build_label_idx(insts)
            self.idx2labels = idx2labels
            self.label2idx = label2idx
        else:
            # for dev/test dataset we don't build label2idx, pass in label2idx argument
            assert label2idx is not None
            self.label2idx = label2idx
            check_all_labels_in_dict(insts=insts, label2idx=self.label2idx)
        self.inst_ids: List[Feature] = []
        # self.convert_instances_to_feature_tensors()

    def convert_instances_to_feature_tensors(self, word2idx: Dict[str, int]):
        self.inst_ids = []
        for i, inst in enumerate(self.insts):
            words = inst.words
            word_ids = []
            for word in words:
                if word in word2idx:
                    word_ids.append(word2idx[word])
                else:
                    word_ids.append(word2idx[UNK])

            # TODO: convert to tensors
            self.inst_ids.append(
                Feature(
                    words=word_ids,
                    seq_len=len(words),
                    label=self.label2idx[inst.label] if inst.label else None
                )
            )

    def read_txt(self, file: str, replace_digits) -> List[Instance]:
        print(f"[Data Info] Reading file: {file}")
        insts = []
        with open(file, 'r', encoding='utf-8') as f:
            for index, line in tqdm(enumerate(f.readlines())):
                if index == 0:
                    continue
                sparts = line.strip().split(",")
                sentence = sparts[5].replace("_comma_", ",")
                if replace_digits:
                    sentence = re.sub('\d', '0', sentence)
                # convert sentence to words, tokenize
                # TODO: fix tokenization
                words = self.tokenizer(sentence)
                label = sparts[2]
                insts.append(Instance(sentence, words, label))
        print("number of sentences: {}".format(len(insts)))
        return insts

    def __len__(self):
        return len(self.inst_ids)

    def __getitem__(self, index):
        return self.inst_ids[index]

    # TODO: fix logic, mostly not supported in older versions
    # def collate_fn(self, batch: List[Feature]):
    #     word_seq_lens = [len(feature.words) for feature in batch]
    #     max_seq_len = max(word_seq_lens)
    #     max_char_seq_len = -1
    #     for feature in batch:
    #         curr_max_char_seq_len = max(feature.char_seq_lens)
    #         max_char_seq_len = max(curr_max_char_seq_len, max_char_seq_len)
    #     for i, feature in enumerate(batch):
    #         padding_length = max_seq_len - len(feature.words)
    #         words = feature.words + [0] * padding_length
    #         chars = []
    #         char_seq_lens = feature.char_seq_lens + [1] * padding_length
    #         for word_idx in range(feature.word_seq_len):
    #             pad_char_length = max_char_seq_len - feature.char_seq_lens[word_idx]
    #             word_chars = feature.chars[word_idx] + [0] * pad_char_length
    #             chars.append(word_chars)
    #         for _ in range(max_seq_len - feature.word_seq_len):
    #             chars.append([0] * max_char_seq_len)
    #         labels = feature.labels + [0] * padding_length if feature.labels is not None else None
    # 
    #         batch[i] = Feature(words=np.asarray(words),
    #                            chars=np.asarray(chars), char_seq_lens=np.asarray(char_seq_lens),
    #                            context_emb=feature.context_emb,
    #                            word_seq_len=feature.word_seq_len,
    #                            labels=np.asarray(labels) if labels is not None else None)
    #     results = Feature(
    #         *(default_collate(samples) if not check_all_obj_is_None(samples) else None for samples in zip(*batch)))
    #     return results
