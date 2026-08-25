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
    print("📝 [1] 8대 전 클러스터 포괄 퀀트 데이터셋 생성 중...")
    train_p, valid_p = build_datasets()
    print(f"✅ 데이터셋 생성 완료 ({train_p}, {valid_p})")

    print("\n🚀 [2] M5 Metal GPU 16GB 메모리 최적화 LoRA 학습 시작...")
    success = MLXLoRATrainer.train(iters=100, batch_size=1, lora_layers=8)
    if success:
        print("🎉 8대 전 클러스터 LoRA 파인튜닝 학습 성공 완료!")
    else:
        print("❌ 학습 실패")

if __name__ == "__main__":
    main()
