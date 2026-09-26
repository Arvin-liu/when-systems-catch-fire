# Supplemental record CASE06

Source type: local event-status recorder. Synthetic.

Purpose: record a selected station's result and preserve any unresolved status.

Procedure:
1. [S01] Record the event ID and attendee identifier presented.
2. [S02] Record the station selected by the authorized operator.
3. [S03] Save the returned token status or roster evidence source with its timestamp.
4. [S04] Record any correction as a separate event with its source.
5. [S05] Stop on a station error; record the returned response and status verbatim.

Observable fields: event ID, attendee identifier, station, token status, roster evidence source, timestamp, final status.
