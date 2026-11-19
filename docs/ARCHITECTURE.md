# Architecture

## Components

### `mseed.py`
Reads MiniSEED using ObsPy, calculates trace statistics, and inserts file,
network, station, channel, segment, and sample records.

### `db.py`
Owns SQLite connection management and upsert helpers.

### `station_api.py`
Calls the FDSN station service and converts station metadata to a normalized
Pandas DataFrame.

### `visualize.py`
Creates metadata CSVs, helicorder-style charts, and a Folium map.

### `pipeline.py`
Orchestrates ingestion, API enrichment, reporting, and visualization.

### `run_pipeline.py`
Command-line entry point.

## Separation of concerns

The application is deliberately divided into:

```text
I/O          -> mseed.py / station_api.py
Persistence  -> db.py + sql/schema.sql
Business flow -> pipeline.py
Presentation -> visualize.py
CLI          -> run_pipeline.py
```

This makes individual pieces testable and easier to replace.

## Error handling

The local MiniSEED files are required and cause the pipeline to fail clearly
if they are missing.

The external station API is treated as an external dependency. A temporary
API failure produces a warning while allowing local MiniSEED processing to
complete. A map can only contain stations for which coordinates are available.
