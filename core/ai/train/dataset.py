import json
import torch
import numpy as np
from torch.utils.data import Dataset
from core.ai.train.model import calculate_delta_e

class PaletteRankingDataset(Dataset):
    """
    A PyTorch Dataset for color palette ranking.

    Each sample represents ONE image and contains a fixed set of color candidates.
    The dataset is designed for ranking-based learning.

    Key design ideas :
    - Multi-source candidates ( GWO / KMeans / Saliency )
    - Rich feature engineering ( color + visual heuristics + context )
    - Binary labels with importance weighting ( derived from user ranking )
    """

    def __init__(self, json_path):
        """
        Parses `training_data.json` into Image Groups.
        Each sample from Dataset represents ONE Image containing 30 candidates.
        Allows for Pairwise Ranking Loss and Context-Aware features.
        """
        self.image_groups = []  # List of dicts : {'features': (30, 19), 'labels': (30, 1), 'weights': (30, 1), 'metadata': [...]}
        print(f"🪻 ||||||  Loading data from {json_path}...  |||||| 🪻")
        self._load_data(json_path)

    def _load_data(self, json_path):
        """
        Load raw JSON data and convert each image entry into a structured group.
        The output is stored in self.image_groups
        """

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for item in data:
            self._process_image_item(item)
            
        print(f"🪻 ||||||  Loaded {len(self.image_groups)} images with candidate groups  |||||| 🪻")

    def _process_image_item(self, item):
        """
        Convert one image entry into a ranking group.

        Steps :
        1. Extract user-selected target colors (ground truth)
        2. Gather candidate colors from multiple sources
        3. Build feature vectors for each candidate
        4. Assign labels and weights
        """

        # Flatten target colors for binary label matching
        targets = []
        if "user_selected_colors" in item:
            for color in item["user_selected_colors"]:
                lab = [color["oklab"]["L"], color["oklab"]["a"], color["oklab"]["b"]]
                rank = color["rank"] # User ranking ( 1 = best )
                # Convert rank → weight ( higher importance for top-ranked colors )
                weight = 11 - rank # Rank 1 -> weight 10, Rank 10 -> weight 1
                targets.append({"lab": lab, "weight": weight})

        visual_dim_oklab = item.get("visual_dimensions_oklab", {})
        visual_rankings = item.get("visual_rankings", {})
        
        def _get_metric_for_color(target_lab, metric_list_name, sub_metric='score'):
            """
            Retrieve a precomputed visual metric for a given color.

            Matching is done via Delta E in OKLab space.

            Args :
                target_lab: color to match
                metric_list_name : which ranking/metric list to search
                sub_metric : which value to extract from matched entry

            Returns :
                float : metric value (default = 0.0 if not found)
            """

            best_score = 0.0
            if metric_list_name in visual_dim_oklab:
                lst = visual_dim_oklab[metric_list_name].get("top_colors", [])
            elif metric_list_name in visual_rankings:
                lst = visual_rankings[metric_list_name]
            else:
                return best_score
                
            for c in lst:
                candidate_lab = [c["oklab"]["L"], c["oklab"]["a"], c["oklab"]["b"]]
                if calculate_delta_e(target_lab, candidate_lab) < 0.01:
                    best_score = float(c.get(sub_metric, 0.0))
                    break
            return best_score

        # Collect 30 candidate colors
        candidates = []
        # Each source contributes candidates + one-hot identity
        for src_name, one_hot in [("gwo_colors", [1,0,0]), ("kmeans_colors", [0,1,0]), ("saliency_colors", [0,0,1])]:
            if src_name in item:
                for color in item[src_name]:
                    candidates.append({"color": color, "source": one_hot, "source_name": src_name})

        if not candidates:
            return

        # Convert all candidates into LAB array for vectorized computation
        all_labs = np.array([[c["color"]["oklab"]["L"], c["color"]["oklab"]["a"], c["color"]["oklab"]["b"]] for c in candidates])
        
        # Global mean color ( used for context-aware features )
        mean_lab = np.mean(all_labs, axis=0)

        img_features = []
        img_labels = []
        img_weights = []
        img_metadata = []

        # Construct features and labels for each candidate
        for i, c in enumerate(candidates):
            lab = all_labs[i]
            rank_in_src = c["color"]["rank"]
            
            # Base aesthetic features
            f_source = c["source"]
            f_rank_scaled = max(0.0, 1.0 - (rank_in_src - 1) / 9.0)
            f_l, f_a, f_b = lab
            f_chroma = float(np.sqrt(f_a**2 + f_b**2))
            
            f_area = _get_metric_for_color(lab, "physical_area_ratio", "score")
            f_sim_area = _get_metric_for_color(lab, "similar_color_area_sum", "score")
            f_ch_saliency = _get_metric_for_color(lab, "chroma_saliency", "score")
            f_l_ratio = _get_metric_for_color(lab, "lightness_ratio", "score")
            f_dom = _get_metric_for_color(lab, "dominant_main_color_ranking", "area_ratio")
            f_viv = _get_metric_for_color(lab, "vividness_ranking", "chroma")
            f_bright = _get_metric_for_color(lab, "brightness_ranking", "lightness")
            
            # Context-Aware Features
            other_labs = np.delete(all_labs, i, axis=0) # Remove current color to compare against others
            dists_to_others = np.linalg.norm(other_labs - lab, axis=-1) # Pairwise distances in perceptual space
            min_dist = float(np.min(dists_to_others)) if len(dists_to_others) > 0 else 0.0 # Nearest neighbor distance ( uniqueness )
            mean_dist = float(np.mean(dists_to_others)) if len(dists_to_others) > 0 else 0.0 # Average distance ( global dispersion )
            local_density = float(np.sum(dists_to_others < 0.03)) # Local density ( how crowded the region is )
            dist_to_mean = float(np.linalg.norm(lab - mean_lab)) # Distance to global mean ( outlier measure )

            vec = f_source + [
                f_rank_scaled, f_l, f_a, f_b, f_chroma,
                f_area, f_sim_area, f_ch_saliency, f_l_ratio,
                f_dom, f_viv, f_bright,
                min_dist, mean_dist, local_density, dist_to_mean
            ] # 3 + 12 + 4 = 19 dims
            
            # Target Label ( Binary ) & Weight
            label = 0.0
            weight = 1.0 # default weight for negative samples
            # If matches user-selected color => positive
            for t in targets:
                if calculate_delta_e(lab, t["lab"]) < 0.01:
                    label = 1.0
                    weight = float(t["weight"])
                    break
                    
            img_features.append(vec)
            img_labels.append([label])
            img_weights.append([weight])
            img_metadata.append({"image": item.get("image_name"), "lab": lab.tolist(), "src": c["source_name"]})

        self.image_groups.append({
            "features": np.array(img_features, dtype=np.float32),
            "labels": np.array(img_labels, dtype=np.float32),
            "weights": np.array(img_weights, dtype=np.float32),
            "metadata": img_metadata,
            "target_labs": [t["lab"] for t in targets] if targets else []
        })

    def __len__(self):
        return len(self.image_groups)
        
    def __getitem__(self, idx):
        grp = self.image_groups[idx]
        return (
            torch.tensor(grp["features"]),
            torch.tensor(grp["labels"]),
            torch.tensor(grp["weights"]),
            idx  # passing idx to retrieve metadata easily if needed
        )
