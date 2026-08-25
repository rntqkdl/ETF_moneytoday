"""
run_lora_train.py
Apple Silicon M5 Metal GPU 직접 가속 Qwen 2.5 LoRA 파인튜닝 실행기 (최신 MLX-LM 규격)
"""

import subprocess
import sys
import os

def run_training():
    print("=" * 70)
    print("🚀 [Apple MLX LoRA] Qwen 2.5 연금형 ETF 퀀트 파인튜닝 학습 시작 (M5 Metal GPU)")
    print("=" * 70)

    model_name = "mlx-community/Qwen2.5-7B-Instruct-4bit"
    data_dir = "./data"
    adapter_path = "./adapters/pension_qwen7b_lora"
    
    os.makedirs("./adapters", exist_ok=True)

    venv_bin = os.path.dirname(sys.executable)
    mlx_cmd = os.path.join(venv_bin, "mlx_lm.lora")
    if not os.path.exists(mlx_cmd):
        mlx_cmd = "mlx_lm.lora"

    cmd = [
        mlx_cmd,
        "--model", model_name,
        "--data", data_dir,
        "--train",
        "--fine-tune-type", "lora",
        "--batch-size", "2",
        "--num-layers", "16",
        "--iters", "200",
        "--learning-rate", "1e-4",
        "--val-batches", "5",
        "--steps-per-report", "20",
        "--steps-per-eval", "50",
        "--save-every", "100",
        "--adapter-path", adapter_path
    ]

    print(f"📌 실행 명령어: {' '.join(cmd)}")
    print("⏳ 모델 가중치 로드 및 Apple M5 Metal GPU 파인튜닝 진행 중...")
    
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    if result.returncode == 0:
        print("\n" + "=" * 70)
        print(f"🎉 Qwen 2.5 LoRA 파인튜닝 학습 성공 완료! 어댑터 저장 위치: {adapter_path}")
        print("=" * 70)
    else:
        print(f"\n❌ 학습 중 오류 발생 (Exit Code: {result.returncode})")

if __name__ == "__main__":
    run_training()
