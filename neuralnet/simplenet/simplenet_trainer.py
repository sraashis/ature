import numpy as np
import torch
from torch.autograd import Variable

from neuralnet.torchtrainer import NNTrainer


class SimpleNNTrainer(NNTrainer):
    def __init__(self, model=None, checkpoint_dir=None, checkpoint_file=None, to_tensorboard=False):
        NNTrainer.__init__(self, model=model, checkpoint_dir=checkpoint_dir, checkpoint_file=checkpoint_file,
                           to_tensorboard=to_tensorboard)

    def evaluate(self, dataloader=None, use_gpu=False, force_checkpoint=False, save_best=False):

        self.model.eval()
        self.model.cuda() if use_gpu else self.model.cpu()

        correct = 0
        total = 0
        accuracy = 0.0

        all_predictions = []
        all_scores = []
        all_labels = []
        all_IDs = []
        all_patchIJs = []
        print('\nEvaluating...')

        ##### Segment Mode only to use while testing####
        segment_mode = dataloader.dataset.segment_mode
        for i, data in enumerate(dataloader, 0):
            if segment_mode:
                IDs, IJs, inputs, labels = data
            else:
                inputs, labels = data
            inputs = inputs.cuda() if use_gpu else inputs.cpu()
            labels = labels.cuda() if use_gpu else labels.cpu()

            outputs = self.model(Variable(inputs))
            _, predicted = torch.max(outputs.data, 1)

            # Save scores
            all_predictions += predicted.numpy().tolist()
            all_scores += outputs.data.numpy().tolist()
            all_labels += labels.numpy().tolist()

            ###### For segment mode only ##########
            if segment_mode:
                all_IDs += IDs.numpy().tolist()
                all_patchIJs += IJs.numpy().tolist()
            ##### Segment mode End ###############

            total += labels.size(0)
            correct += (predicted == labels).sum()
            accuracy = round(100 * correct / total, 2)
            print('_________ACCURACY___of___[%d/%d]batches: %.2f%%' % (i + 1, dataloader.__len__(), accuracy), end='\r')

            ########## Feeding to tensorboard starts here...#####################
            ####################################################################
            if self.to_tenserboard:
                step = next(self.res['val_counter'])
                self.logger.scalar_summary('accuracy/validation', accuracy, step)
            #### Tensorfeed stops here# #########################################
            #####################################################################

        print()
        all_IDs = np.array(all_IDs, dtype=np.int)
        all_patchIJs = np.array(all_patchIJs, dtype=np.int)
        all_scores = np.array(all_scores)
        all_predictions = np.array(all_predictions)
        all_labels = np.array(all_labels)

        self._save_if_better(save_best=save_best, force_checkpoint=force_checkpoint, accuracy=accuracy)

        if segment_mode:
            return all_IDs, all_patchIJs, all_scores, all_predictions, all_labels
        return all_predictions, all_labels