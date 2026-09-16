# Privacy & Security

## API Key

- Read from `ARK_API_KEY` environment variable only
- Never ask user to paste key in chat
- Never logged, printed, or written to files
- Error messages never echo the key

## Private Data

- Workspace is outside the git repo (`CAT_STICKER_HOME`)
- Private cat photos never committed
- EXIF GPS/camera data checked on tracked images

## Privacy Check

Run: `cat-sticker privacy-check`

Scans git-tracked files for:
- API keys / secrets
- Private absolute paths
- EXIF GPS in tracked images
- Bearer tokens
