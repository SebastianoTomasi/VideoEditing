# Recordings move into their video's folder and are deleted only on request

Original recordings used to stay in the OBS folder, never moved or deleted,
because they are the only copy. The OBS folder then filled with recordings of
200–300 MB each, long after their videos were published. Now, once the user
confirms which recordings make up a video, they move into the video's folder
with their OBS names and their transcripts. They are deleted only when the user
asks to delete the originals, and only those of videos whose edit is final.
They go to the Recycle Bin, which the user empties.

## Considered options

- **Deleting the recordings as soon as the edit is final:** rejected, because
  the user may still want a correction after publishing.
- **Asking the user after some time whether to delete them:** rejected as too
  complex for one user who notices when the disk is full.
- **Renaming the moved recordings:** rejected, because the OBS name already
  carries the date and time of the recording.

## Consequences

Once a video's recordings are deleted, its edit can no longer be corrected or
rendered again. The edit, the cut list, the subtitles, the description, and the
thumbnails stay.
