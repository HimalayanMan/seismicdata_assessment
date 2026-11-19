# Database Design

## Tables

### `network`
Stores seismic network identity.

- `network_id` — PK
- `code` — unique network code

### `station`
Stores station identity and location.

- `station_id` — PK
- `network_id` — FK to `network`
- `code` — station code
- latitude/longitude/elevation
- site name
- unique `(network_id, code)`

### `channel`
Stores channel identity.

- `channel_id` — PK
- `station_id` — FK to `station`
- location code
- channel code
- sample rate
- unique `(station_id, location_code, code)`

### `file`
Stores source-file provenance.

- `file_id` — PK
- absolute path
- filename
- SHA-256
- import timestamp

### `waveform_segment`
Stores one logical trace/segment.

- `segment_id` — PK
- source file FK
- channel FK
- start/end time
- sample count
- sample rate
- min/max/mean

### `sample`
Stores waveform observations.

- composite PK `(segment_id, sample_index)`
- segment FK
- timestamp
- value

## Normalization

The design avoids repeating network/station/channel metadata for every sample.

A sample references a segment; a segment references a channel; a channel
references a station; a station references a network.

This separates entity metadata from time-series observations and provides
clear referential integrity.

## Useful queries

See `sql/queries.sql`.
