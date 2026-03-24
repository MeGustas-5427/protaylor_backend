EXPORT = uv export --no-hashes --no-header --no-annotate --no-dev --format requirements.txt > requirements.txt

add:
	uv add $(pkg) && $(EXPORT)

remove:
	uv remove $(pkg) && $(EXPORT)

lock:
	uv lock && $(EXPORT)

sync:
	uv sync && $(EXPORT)
