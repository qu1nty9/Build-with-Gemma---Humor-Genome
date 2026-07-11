from __future__ import annotations

import argparse
import asyncio

from app.config import settings
from app.gemma import OllamaGemmaGateway
from app.pipeline import HumorGenomePipeline
from app.schemas import AnalyzeRequest, ComedyGene, FlowRequest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Humor Genome Lab text pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser("analyze", help="Analyze one joke into a HumorGenome.")
    analyze.add_argument("--text", required=True)
    flow = subparsers.add_parser("flow", help="Run analyze, mutate, and compare.")
    flow.add_argument("--text", required=True)
    flow.add_argument("--target-gene", choices=[gene.value for gene in ComedyGene], required=True)
    flow.add_argument("--variants", type=int, default=2, choices=[2, 3])
    return parser


async def run_flow(args: argparse.Namespace) -> None:
    pipeline = HumorGenomePipeline(OllamaGemmaGateway(settings))
    result = await pipeline.flow(
        FlowRequest(
            text=args.text,
            target_gene=ComedyGene(args.target_gene),
            number_of_variants=args.variants,
        )
    )
    print(result.model_dump_json(indent=2))


async def run_analyze(args: argparse.Namespace) -> None:
    pipeline = HumorGenomePipeline(OllamaGemmaGateway(settings))
    result = await pipeline.analyze(AnalyzeRequest(text=args.text))
    print(result.model_dump_json(indent=2))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "analyze":
        asyncio.run(run_analyze(args))
    elif args.command == "flow":
        asyncio.run(run_flow(args))


if __name__ == "__main__":
    main()
