"""
scripts/train_lora.py
Apple Silicon M5 Metal GPU 기반 Qwen 2.5 LoRA 파인튜닝 학습 실행 스크립트
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ai.dataset_builder import build_datasets
from src.ai.lora_trainer import MLXLoRATrainer

def main():
    print("📝 [1] 퀀트 파인튜닝 데이터셋 생성 중...")
    train_p, valid_p = build_datasets()
    print(f"✅ 데이터셋 생성 완료 ({train_p}, {valid_p})")

    print("\n🚀 [2] M5 Metal GPU LoRA 파인튜닝 학습 시작...")
    success = MLXLoRATrainer.train(iters=200, batch_size=2, lora_layers=16)
    if success:
        print("🎉 LoRA 파인튜닝 학습 성공 완료!")
    else:
        print("❌ 학습 실패")

if __name__ == "__main__":
    main()
