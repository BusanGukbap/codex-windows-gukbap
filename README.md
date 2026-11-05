# Codex Windows Gukbap

This is a personal Windows/Codex adaptation of [thecasterian/claude-code](https://github.com/thecasterian/claude-code), obtained through the user's [fork](https://github.com/BusanGukbap/claude-code-steal). Personal changes are maintained in the private [codex-windows-gukbap](https://github.com/BusanGukbap/codex-windows-gukbap) repository. See [README-CODEX.md](README-CODEX.md) for native Windows setup, installation previews, and compatibility limits. Neither upstream nor the original fork is updated by this personal version.

The original Claude Code integrations below remain reference material. Do not copy `settings.json` into Codex configuration.

The 16 adapted core skills are complemented by an opt-in collection of 6 user-selected personal skill snapshots under `personal-skills/`. See [the optional collection](README-CODEX.md#optional-frequently-used-personal-skills) before enabling it; the default installer remains core-only.

## Original Claude Code reference

## Plugins

- `learning-output-style`
- `clarify`
```bash
# Install
/plugin marketplace add team-attention/plugins-for-claude-natives
/plugin install clarify
```
- `clangd-lsp` — C/C++ language server providing code intelligence, diagnostics, and formatting
```bash
# Install (requires clangd on PATH)
/plugin install clangd-lsp

# Install clangd if not present
# macOS: brew install llvm
# Ubuntu/Debian: sudo apt install clangd
# Fedora: sudo dnf install clang-tools-extra
# Arch Linux: sudo pacman -S clang
```

## MCPs

- Context7
```bash
claude mcp add context7 --scope user -- npx -y @upstash/context7-mcp --api-key <YOUR_API_KEY>
```
