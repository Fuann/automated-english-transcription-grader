import numpy as np
import scipy.stats as stats
import torch
import torch.nn as nn

def get_losses(training_objectives, training_objective_predictions, labels, device):
    """
    Returns a dict containing training objectives and their respective losses over their predictions and the combined
    weighted loss of the training objectives.
    """
    losses = {'overall': torch.tensor([0.], device=device)}
    for objective, prediction in training_objective_predictions.items():
        _, alpha = training_objectives[objective]
        # Scoring objective uses MSE loss and all other objectives use CrossEntropy loss
        #criterion = nn.MSELoss().to(device) if objective == 'score' else nn.CrossEntropyLoss(
        #    ignore_index=-1).to(device)
        
        criterion = nn.CrossEntropyLoss(ignore_index=-1).to(device)
        batch_labels = labels[objective].reshape(-1).long()
        #print(batch_labels.shape)
        #print(batch_labels)
        losses[objective] = criterion(prediction, batch_labels)
        losses['overall'] += (losses[objective] * alpha)
        
        #if objective == 'score':
        #    rand_indices = torch.randperm(batch_labels.size()[0])
        #    if rand_indices.shape[0] > 1:
        #        prediction_shuffle = prediction[rand_indices]
        #        batch_labels_shuffle = batch_labels[rand_indices]
        #        prediction_interval = torch.abs(prediction - prediction_shuffle)
        #        batch_labels_interval = torch.abs(batch_labels - batch_labels_shuffle)
        #        losses['score_l2r'] = criterion(prediction_interval, batch_labels_interval)
        #        losses['overall'] = 0.9 * losses['overall'] + 0.1 * losses['score_l2r']

    return losses

def compute_metrics(total_losses, all_score_predictions, all_score_targets, device):
    """ Computes Pearson correlation and accuracy within 0.5 and 1 of target score and adds each to total_losses dict. """
    total_losses['pearson'] = stats.pearsonr(all_score_predictions.cpu(), all_score_targets.cpu())[0]
    total_losses['within_0.5'] = _accuracy_within_margin(all_score_predictions, all_score_targets, 0.5,
                                                              device)
    total_losses['within_1'] = _accuracy_within_margin(all_score_predictions, all_score_targets, 1,
                                                                device)

def _accuracy_within_margin(score_predictions, score_target, margin, device):
    """ Returns the percentage of predicted scores that are within the provided margin from the target score. """
    return torch.sum(
        torch.where(
            torch.abs(score_predictions - score_target) <= margin,
            torch.ones(len(score_predictions), device=device),
            torch.zeros(len(score_predictions), device=device))).item() / len(score_predictions) * 100

