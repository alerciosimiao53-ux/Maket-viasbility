# smart_market_intelligence

## Run
```bash
python main.py --date today
```

This generates:
- `reports/YYYY-MM-DD/dashboard.html`
- `reports/YYYY-MM-DD/report.html`
- `reports/YYYY-MM-DD/index.html` (redirects to dashboard)

## Optional real ticker data (Finnhub)
Set environment variable before running:
```bash
export FINNHUB_API_KEY="your_api_key_here"
python main.py --date today
```
If no key is provided, the system automatically uses the demo ticker provider.
