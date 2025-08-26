# macOS Work Archive

This directory contains all the macOS-specific work for XDS110 debugging:

## What's Here:
- Docker containerization attempts
- USB/IP bridge solutions  
- Host bridge for XDS110 access
- macOS USB driver workarounds
- Error -260 troubleshooting

## Why Moved:
These solutions were specific to overcoming macOS limitations.
Linux doesn't need these workarounds - TI tools work natively.

## Key Findings:
- XDS110 detected at Serial: LS4104RF
- Uptime counter is at 0x00000C00
- macOS Error -260 blocks all TI debug tools
- Docker + USB/IP bridge was partially successful

## Next: Use Linux
On Linux, simple commands like these should work:
```bash
dslite --config TMS320F280039C_LaunchPad.ccxml --memory-read 0x00000C00 4
```

