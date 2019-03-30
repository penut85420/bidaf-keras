from keras.utils import Sequence
import os
import numpy as np
from .magnitude import MagnitudeVectors


class BatchGenerator(Sequence):
    'Generates data for Keras'

    vectors = None

    def __init__(self, gen_type, batch_size, emdim, squad_version, shuffle):
        'Initialization'

        base_dir = os.path.join(os.path.dirname(__file__), os.pardir, 'data')

        self.vectors = MagnitudeVectors(base_dir, emdim).load_vectors()
        self.squad_version = squad_version

        self.context_file = os.path.join(base_dir, 'squad', gen_type + '-v{}.context'.format(squad_version))
        self.question_file = os.path.join(base_dir, 'squad', gen_type + '-v{}.question'.format(squad_version))
        self.span_file = os.path.join(base_dir, 'squad', gen_type + '-v{}.span'.format(squad_version))
        if self.squad_version == 2.0:
            self.is_impossible_file = os.path.join(base_dir, 'squad', gen_type + '-v{}.is_impossible'.format(squad_version))

        self.batch_size = batch_size
        i = 0
        with open(self.span_file, 'r', encoding='utf-8') as f:

            for i, _ in enumerate(f):
                pass
        self.num_of_batches = (i + 1) // self.batch_size
        self.indices = np.arange(i + 1)
        self.shuffle = shuffle

    def __len__(self):
        'Denotes the number of batches per epoch'
        return self.num_of_batches

    def __getitem__(self, index):
        'Generate one batch of data'
        # Generate indexes of the batch
        start_index = (index * self.batch_size) + 1
        end_index = ((index + 1) * self.batch_size) + 1

        inds = self.indices[start_index:end_index]

        contexts = []
        with open(self.context_file, 'r', encoding='utf-8') as cf:
            for i, line in enumerate(cf, start=1):
                line = line[:-1]
                if i in inds:
                    contexts.append(line.split(' '))

        questions = []
        with open(self.question_file, 'r', encoding='utf-8') as qf:
            for i, line in enumerate(qf, start=1):
                line = line[:-1]
                if i in inds:
                    questions.append(line.split(' '))

        answer_spans = []
        with open(self.span_file, 'r', encoding='utf-8') as sf:
            for i, line in enumerate(sf, start=1):
                line = line[:-1]
                if i in inds:
                    answer_spans.append(line.split(' '))

        if self.squad_version == 2.0:
            is_impossible = []
            with open(self.is_impossible_file, 'r', encoding='utf-8') as isimpf:
                for i, line in enumerate(isimpf, start=1):
                    line = line[:-1]
                    if i in inds:
                        is_impossible.append(line)

            for i, flag in enumerate(is_impossible):
                contexts[i].append("unanswerable")
                if flag == "1":
                    answer_spans[i] = [len(contexts[i])-1, len(contexts[i])-1]

        context_batch = self.vectors.query(contexts)
        question_batch = self.vectors.query(questions)
        span_batch = np.expand_dims(np.array(answer_spans, dtype='float32'), axis=1)
        return [context_batch, question_batch], [span_batch]

    def on_epoch_end(self):
        if self.shuffle:
            np.random.shuffle(self.indices)
