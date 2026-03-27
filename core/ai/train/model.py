import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class AestheticScorerMLP(nn.Module):
    """
    Aesthetic Scoring Model for Color Candidate Ranking.

    This model scores each candidate color independently based on engineered features.
    It is designed for learning-to-rank tasks with :
    - Pointwise supervision ( binary classification )
    - Pairwise ranking constraints

    Input :
        (batch_size, num_candidates, 19)

    Output :
        (batch_size, num_candidates, 1) => raw logits
    """
    def __init__(self, input_dim=19):
        super(AestheticScorerMLP, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.LayerNorm(64),
            nn.SiLU(),
            nn.Dropout(p=0.2),
            
            nn.Linear(64, 32),
            nn.LayerNorm(32),
            nn.SiLU(),
            nn.Dropout(p=0.1),
            
            nn.Linear(32, 16),
            nn.LayerNorm(16),
            nn.SiLU(),
            
            nn.Linear(16, 1)
        )
        
    def forward(self, x):
        """
        Forward pass.

        Args :
            x: Tensor of shape (batch_size, num_candidates, input_dim)

        Returns :
            logits: Tensor of shape (batch_size, num_candidates, 1)

        Note :
            The model treats each candidate independently ( shared weights ),
            but ranking relationships are enforced via the loss function.
        """
        return self.net(x)

    def predict_proba(self, x):
        """
        Convert logits into probabilities for inference.

        Useful for :
        - ranking candidates
        - post-processing ( e.g., NMS )

        Returns :
            probabilities in range [0, 1]
        """

        with torch.no_grad():
            logits = self.forward(x)
            return torch.sigmoid(logits)

# Utility : Color Distance

def calculate_delta_e(lab1, lab2):
    """
    Compute perceptual color distance in OKLab space.

    This is used for :
    - matching colors ( ground truth alignment )
    - diversity filtering ( NMS )

    Returns :
        Euclidean distance
    """

    return np.linalg.norm(np.array(lab1) - np.array(lab2), axis=-1)

# Post-processing : NMS

def apply_nms(candidates, scores, max_colors=10, similarity_threshold=0.03):
    """
    Non-Maximum Suppression ( NMS ) for color selection.

    Purpose :
        Remove visually redundant colors while preserving high-scoring ones.

    Strategy :
        1. Sort candidates by score ( descending )
        2. Iteratively select candidates
        3. Reject candidates too similar to already selected ones

    Args :
        candidates: list of color dicts
        scores: predicted scores
        max_colors: number of colors to keep
        similarity_threshold: distance threshold in OKLab space

    Returns :
        List of selected color candidates
    """

    selected = []
    sorted_indices = np.argsort(scores)[::-1]
    
    for idx in sorted_indices:
        if len(selected) >= max_colors:
            break
            
        candidate = candidates[idx]
        lab = [candidate['oklab']['L'], candidate['oklab']['a'], candidate['oklab']['b']]
        
        too_similar = False
        for sel in selected:
            sel_lab = [sel['oklab']['L'], sel['oklab']['a'], sel['oklab']['b']]
            if calculate_delta_e(lab, sel_lab) < similarity_threshold:
                too_similar = True
                break
                
        if not too_similar:
            selected.append(candidate)
            
    # Fallback : ensure enough colors are returned
    if len(selected) < max_colors:
        for idx in sorted_indices:
            if candidates[idx] not in selected:
                selected.append(candidates[idx])
                if len(selected) >= max_colors:
                    break
                    
    return selected

# Loss Function

class CombinedRankingLoss(nn.Module):
    """
    Hybrid loss for learning-to-rank.

    Combines :
    1. Pointwise loss ( BCE ) : learns absolute quality
    2. Pairwise loss: enforces relative ordering

    Final loss :
        Loss = BCE + λ * RankingLoss
    """

    def __init__(self, margin=0.5, lambda_rank=1.0):
        super().__init__()
        self.margin = margin
        self.lambda_rank = lambda_rank
        
    def forward(self, logits, labels, weights):
        """
        logits : (batch, num_candidates, 1)
        labels : (batch, num_candidates, 1) - 1.0 or 0.0
        weights : (batch, num_candidates, 1)
        """
        # 1. BCE With Logits Loss ( weighted by Rank Importance )
        bce_loss = F.binary_cross_entropy_with_logits(logits, labels, weight=weights, reduction='mean')
        
        # 2. Pairwise Ranking Loss ( Per Image in Batch )
        rank_loss = 0.0
        batch_size = logits.size(0)
        valid_pairs = 0
        
        for b in range(batch_size):
            lgt = logits[b].squeeze()
            lbl = labels[b].squeeze()
            
            pos_indices = torch.where(lbl == 1.0)[0]
            neg_indices = torch.where(lbl == 0.0)[0]
            
            if len(pos_indices) > 0 and len(neg_indices) > 0:
                # Compare every positive to every negative
                pos_logits = lgt[pos_indices].unsqueeze(1) # (N_pos, 1)
                neg_logits = lgt[neg_indices].unsqueeze(0) # (1, N_neg)
                
                # We want pos_logits > neg_logits + margin
                # Margin loss = max(0, margin - (pos - neg))
                diffs = self.margin - (pos_logits - neg_logits)
                pair_losses = torch.clamp(diffs, min=0.0)
                
                rank_loss += pair_losses.mean()
                valid_pairs += 1
                
        if valid_pairs > 0:
            rank_loss = rank_loss / valid_pairs
            
        return bce_loss + self.lambda_rank * rank_loss

def save_model(model, path):
    torch.save(model.state_dict(), path)

def load_model(model, path):
    model.load_state_dict(torch.load(path, weights_only=True))
    model.eval()
    return model
