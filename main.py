from smart_market_intelligence.main import parse_args, run


if __name__ == "__main__":
    args = parse_args()
    run(args.date)
