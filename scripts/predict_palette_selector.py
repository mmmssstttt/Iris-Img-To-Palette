import argparse
import torch
import numpy as np
import scipy.optimize as optimize
from core.ai.train.dataset import PaletteRankingDataset
from core.ai.train.model import AestheticScorerMLP, apply_nms, load_model, calculate_delta_e

def predict_and_evaluate():
    parser = argparse.ArgumentParser(description="Predict top 10 palette colors using AI Scorer")
    parser.add_argument("--data", required=True, help="Path to JSON file containing candidate features")
    parser.add_argument("--model", default="models/palette_scorer.pth", help="Path to trained model")
    parser.add_argument("--sim_threshold", type=float, default=0.02, help="NMS Oklab distance threshold ( Delta E )")
    args = parser.parse_args()

    model = AestheticScorerMLP(input_dim=19)
    try:
        model = load_model(model, args.model)
        print(f"🪻 ||||||  Loaded model from {args.model}  |||||| 🪻")
    except FileNotFoundError:
        print(f"Model file not found at {args.model}. Please train the model first.")
        return

    # Load grouped dataset
    dataset = PaletteRankingDataset(args.data)
    if len(dataset) == 0:
        print("No candidate data found.")
        return

    all_precisions = []
    all_avg_dists = []

    for idx in range(len(dataset)):
        features, labels, _, _ = dataset[idx]
        grp = dataset.image_groups[idx]
        meta_list = grp["metadata"]
        target_labs = grp["target_labs"]
        image_name = meta_list[0]['image'] if meta_list and meta_list[0]['image'] else f"Image_{idx}"

        # Predict context-aware batched items
        scores = model.predict_proba(features.unsqueeze(0)).numpy().flatten()
        
        candidates = []
        for i, meta in enumerate(meta_list):
            candidates.append({
                "oklab": {"L": meta["lab"][0], "a": meta["lab"][1], "b": meta["lab"][2]},
                "source": meta["src"],
            })
            
        print(f"\n🪻 ||||||  Output Palette for Image: {image_name}  |||||| 🪻")
        top_10 = apply_nms(candidates, scores, max_colors=10, similarity_threshold=args.sim_threshold)
        
        # Verify Top 10
        pred_labs = []
        for rank, color in enumerate(top_10, 1):
            L, a, b = color['oklab']['L'], color['oklab']['a'], color['oklab']['b']
            pred_labs.append([L, a, b])
            print(f"Rank {rank}: Oklab(L={L:.3f}, a={a:.3f}, b={b:.3f}) | Source: {color['source']}")

        # Evaluation against target user_selected_colors
        if target_labs:
            # 1. Precision@10: Count of predictions matching any target (Delta E < 0.01)
            matches = 0
            for plab in pred_labs:
                if any(calculate_delta_e(plab, tlab) < 0.01 for tlab in target_labs):
                    matches += 1
            p10 = matches / len(top_10) if len(top_10) > 0 else 0
            all_precisions.append(p10)
            
            # 2. Average Distance (Hungarian Matching)
            # Create distance matrix
            cost_matrix = np.zeros((len(pred_labs), len(target_labs)))
            for i, p in enumerate(pred_labs):
                for j, t in enumerate(target_labs):
                    cost_matrix[i, j] = calculate_delta_e(p, t)
            
            # Solve optimal assignment
            row_ind, col_ind = optimize.linear_sum_assignment(cost_matrix)
            matched_dists = cost_matrix[row_ind, col_ind]
            avg_dist = np.mean(matched_dists)
            all_avg_dists.append(avg_dist)
            
            print(f"> Evaluation Metrics:")
            print(f"  Precision@10: {p10*100:.1f}%")
            print(f"  Avg Color Distance (Delta E): {avg_dist:.4f}")

    if all_precisions:
        print("\n🪻 ||||||  OVERALL DATASET EVALUATION  |||||| 🪻")
        print(f"Mean Precision@10: {np.mean(all_precisions)*100:.2f}%")
        print(f"Mean Recall@10:    {np.mean(all_precisions)*100:.2f}% (Since K matches Ground Truth count)")
        print(f"Mean Avg Distance: {np.mean(all_avg_dists):.4f}")

if __name__ == "__main__":
    predict_and_evaluate()
