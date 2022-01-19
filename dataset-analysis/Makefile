retrieve_logs:
	./scripts/retrieve_logs.sh

analyze_traces:
	echo "Requires Python environment with sb"
	sb version
	python scripts/analyze_traces.py

generate_plots:
	python scripts/overview.py
	python scripts/exp1_latency_breakdown.py
	python scripts/exp2_load_levels.py
	python scripts/exp3_invocation_patterns.py

# Generates plots for all endpoints
generate_plots_all:
	python scripts/exp1_latency_breakdown_all.py
	python scripts/exp3_invocation_patterns_all.py
