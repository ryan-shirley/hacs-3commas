# 3Commas for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

This Home Assistant integration allows you to view your 3Commas bot statistics directly in your Home Assistant dashboard. Monitor your trading profits, active deals, and locked funds all in one place.

## Features

- View overall USD profit from your 3Commas bots
- Track today's USD profit
- Monitor active deals USD profit
- See funds locked in active deals
- Support for both HMAC and RSA authentication methods
- Option to select between Paper and Real trading modes

## Screenshots
![Example Dashboard](https://github.com/ryan-shirley/hacs-3commas/raw/main/images/dashboard.png)

## Installation

### HACS (Recommended)

1. Ensure that [HACS](https://hacs.xyz/) is installed.
2. Search for "3Commas" in the HACS Integrations tab.
3. Click Install.
4. Restart Home Assistant.
5. Go to **Settings** → **Devices & Services** and click **+ Add Integration**.
6. Search for "3Commas" and follow the setup instructions.

### Manual Installation

1. Copy the `custom_components/three_commas` directory from this repository to your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Go to **Settings** → **Devices & Services** and click **+ Add Integration**.
4. Search for "3Commas" and follow the setup instructions.

## Configuration

The integration can be configured via the Home Assistant UI:

1. Go to **Settings** → **Devices & Services** and click **+ Add Integration**.
2. Search for "3Commas" and select it.
3. Choose your authentication method:
   - **HMAC Authentication**: Requires API key and API secret
   - **RSA Authentication**: Requires API key and private key (PEM format)
4. Select your trading mode:
   - **Paper Trading**: For using 3Commas in paper trading mode
   - **Real Trading**: For live trading with real funds

## API Keys and Authentication

To use this integration, you'll need to create API keys from your 3Commas account:

1. Log in to your [3Commas account](https://3commas.io/)
2. Go to **API** in your profile settings
3. Create a new API key with "Read" permission
4. For HMAC authentication:
   - Save both the API key and Secret
5. For RSA authentication:
   - Generate an RSA key pair
   - Upload your public key to 3Commas
   - Keep your private key secure for use with this integration

## Troubleshooting

If you encounter issues with the integration:

1. Verify your API credentials are correct and have proper permissions
2. Check that your network allows connections to the 3Commas API
3. For RSA authentication issues, ensure your private key is in the correct PEM format
4. Enable debug logging for more information:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.three_commas: debug
   ```

## Contributing

If you'd like to contribute to this project, please read the [Contributing Guidelines](CONTRIBUTING.md).

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/ryan-shirley/hacs-3commas.svg
[commits]: https://github.com/ryan-shirley/hacs-3commas/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-orange.svg
[license-shield]: https://img.shields.io/github/license/ryan-shirley/hacs-3commas.svg
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40ryan--shirley-blue.svg
[releases-shield]: https://img.shields.io/github/release/ryan-shirley/hacs-3commas.svg
[releases]: https://github.com/ryan-shirley/hacs-3commas/releases
[user_profile]: https://github.com/ryan-shirley
