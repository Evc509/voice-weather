# Changelog

All notable changes to Voice Weather are documented here.

## [3.0.0] - 2026-07-11

### Added

- Responsive local Web interface with current-weather and seven-day forecast cards.
- City sidebar, language selector, refresh control and native macOS voice playback.
- `voice-weather-web` command with automatic browser launch and `--no-browser` mode.
- Local JSON API shared with the existing weather, settings and speech core.

### Security

- Web service binds exclusively to `127.0.0.1` and is not exposed to the local network.

### Improved

- Language changes now reload the full page so every label and subsequent view stays consistent.
- Removed explanatory sublabels beneath city names for a cleaner sidebar.
- Replaced the small legacy default list with geographically distributed cities across seven world regions.
- Added persistent add, replace and delete operations for favorite cities.
- Added geocoded city validation and language-specific display names when adding or replacing cities.
- Added AQI, PM2.5, PM10, UV index and localized health guidance.
- Forecast cards now show localized weekday and date, with expandable precipitation, wind, UV, sunrise and sunset details.
- Web voice playback now uses the same fully localized announcement scripts as the terminal interface.

[3.0.0]: https://github.com/Evc509/voice-weather/releases/tag/v3.0.0

## [2.0.1] - 2026-07-11

### Added

- A macOS launcher that opens interactive sessions in a separate Terminal window.
- Automatic screen clearing before an interactive session and window closing after exit.
- `voice-weather-cli` for users who prefer the current terminal.

### Changed

- Commands with arguments continue to run in the current terminal for scripting compatibility.

[2.0.1]: https://github.com/Evc509/voice-weather/releases/tag/v2.0.1

## [2.0.0] - 2026-07-10

### Added

- Rich color interface with structured panels and weather tables.
- First city slot reserved for an optional IP-derived local city.
- Five selectable text and speech languages: Chinese, English, French, Spanish and Japanese.
- Dynamic detection of installed macOS voices with text-only fallback.
- Versioned settings with automatic migration of existing favorite cities.
- Localized weather advice for precipitation, temperature extremes and strong wind.
- Concise multilingual spoken summaries after interactive forecasts.

### Changed

- Reorganized the main menu around weather, forecasts, cities, language and settings.
- Language and voice preferences persist between sessions.
- Current conditions and forecasts now share the Open-Meteo data source for consistent results.

[2.0.0]: https://github.com/Evc509/voice-weather/releases/tag/v2.0.0

## [1.0.0] - 2026-07-10

### Added

- Bilingual 1–7 day forecasts with daily high and low temperatures, defaulting to seven days.
- Maximum daily rain probability and a representative midday weather summary.
- `--forecast` and `--days` command-line options.
- Forecast access directly from the interactive menu, with city, language and day selection.

### Changed

- Forecasts now use Open-Meteo for a reliable seven-day range; current conditions remain on wttr.in.
- Replaced the mixed city/action prompt with a consistent numbered two-level menu.
- City selection always displays the complete list beginning with `[1]` and includes manual entry and return actions.
- Invalid city configuration is backed up automatically before restoring safe defaults.

[1.0.0]: https://github.com/Evc509/voice-weather/releases/tag/v1.0.0

## [0.1.0] - 2026-07-10

### Added

- Interactive Mandarin and English weather announcements on macOS.
- Configurable shortcut cities stored outside the repository.
- One-shot command-line queries with optional speech suppression.
- Temperature, feels-like temperature, humidity, precipitation, wind and pressure.
- `--version` and `--list-cities` commands.
- Local weather logs under `~/.voice-weather/`.
- Automated tests on Python 3.9, 3.10, 3.11 and 3.12.

### Improved

- Friendly handling for network, speech, keyboard interrupt and invalid-input errors.
- Common weather descriptions translated for Mandarin announcements.

[0.1.0]: https://github.com/Evc509/voice-weather/releases/tag/v0.1.0
