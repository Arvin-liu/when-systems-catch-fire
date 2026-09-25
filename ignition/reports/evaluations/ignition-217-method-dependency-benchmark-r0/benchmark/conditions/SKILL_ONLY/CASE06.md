# Supplemental record CASE06

Source type: local event check-in instruction. Synthetic.

Purpose: record an attendee check-in using the selected station.

Procedure:
1. [S01] Record the event ID and attendee identifier presented.
2. [S02] For a valid event code, scan once and record the returned roster status.
3. [S03] For a no-match response, preserve the response and use the staffed review queue if authorized.
4. [S04] Record any manual correction as a separate event with its source.
5. [S05] Stop if the roster record cannot be resolved; do not invent an attendee match.

Observable fields: event ID, attendee identifier, scan status, queue ID, manual-review source, final recorded status.
