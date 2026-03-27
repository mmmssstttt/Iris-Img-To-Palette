import argparse
import torch
from torch.utils.data import DataLoader
from core.ai.train.dataset import PaletteRankingDataset
from core.ai.train.model import AestheticScorerMLP, CombinedRankingLoss, save_model
import os

def train():
    parser = argparse.ArgumentParser(description="Train the Aesthetic Color Selector")
    parser.add_argument("--data", default="training_data.json", help="Path to JSON training data")
    parser.add_argument("--epochs", type=int, default=150, help="Number of epochs")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--save_path", default="models/palette_scorer.pth", help="Model save path")
    args = parser.parse_args()

    dataset = PaletteRankingDataset(args.data)
    if len(dataset) == 0:
        print("No data parsed. Exiting.")
        return

    # Batch size is number of images. Each image contains 30 candidates.
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

    model = AestheticScorerMLP(input_dim=19)
    criterion = CombinedRankingLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-4)

    model.train()
    print("🪻 ||||||  Starting Training  |||||| 🪻")
    
    for epoch in range(args.epochs):
        total_loss = 0.0
        for features, labels, weights, _ in dataloader:
            optimizer.zero_grad()
            logits = model(features)
            
            loss = criterion(logits, labels, weights)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        if (epoch + 1) % 10 == 0 or epoch == 0:
            avg_loss = total_loss / len(dataloader)
            print(f"Epoch {epoch+1:03d}/{args.epochs} - Loss: {avg_loss:.4f}")

    os.makedirs(os.path.dirname(args.save_path), exist_ok=True)
    save_model(model, args.save_path)
    print(f"🪻 ||||||  Training Complete!  |||||| 🪻")
    print(f"🪻 ||||||  Model saved to {args.save_path}  |||||| 🪻")

if __name__ == "__main__":
    train()
