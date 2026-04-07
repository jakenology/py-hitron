# Getting Started with py-hitron

**py-hitron** is a Python helper tool for querying Hitron cable modems. It connects to your modem's web interface to retrieve and display downstream/upstream channel information, signal strength, and modem status.

## Prerequisites

- Python 3.7 or higher
- Access to your Hitron modem at `192.168.100.1` (default)
- Internet connection to your modem's data API

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/jakenology/py-hitron.git
cd py-hitron
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install the required packages:
- **httpx**: Async HTTP client for API requests
- **rich**: Beautiful terminal output with colors and formatting

## Quick Start

### Running the Tool

py-hitron provides several commands to query your modem:

```bash
# View downstream channels
python main.py ds

# View upstream channels
python main.py us

# View modem status (MAC, uptime, etc.)
python main.py status

# View all information
python main.py all
```

### Understanding the Output

#### Downstream Channels (`ds`)
Shows all downstream channels including:
- **Channel Type**: SC-QAM (DOCSIS 3.0) or OFDM (DOCSIS 3.1)
- **Frequency**: Channel frequency in MHz
- **Power (dBmV)**: Signal power level
- **SNR (dB)**: Signal-to-noise ratio

Power levels are color-coded:
- 🟢 **Green**: Within Midco specs (-6 to +15 dBmV)
- 🔴 **Red**: Outside specs

#### Upstream Channels (`us`)
Shows all upstream channels:
- **Channel Type**: ATDMA (DOCSIS 3.0) or OFDMA (DOCSIS 3.1)
- **Frequency**: Channel frequency in MHz
- **Pwr (+6Adj)**: Signal power with +6dB adjustment for OFDMA

Power levels are color-coded:
- 🟢 **Green**: Within Midco specs (35 to 48 dBmV)
- 🔴 **Red**: Outside specs

#### Modem Status (`status`)
Displays:
- **MAC Address**: Your modem's physical address
- **Uptime**: How long the modem has been running
- **Traffic Status**: Current connection status
- **Spec Check**: Overall health report showing if modem is within manufacturer specifications

## Customizing the Modem IP

By default, py-hitron connects to `192.168.100.1`. To use a different IP:

```python
# In main.py, modify the HitronClient initialization
client = HitronClient(ip="192.168.0.1")  # Your modem's IP
```

## Understanding ISP Specifications

By default, py-hitron checks against **Midco ISP specifications**:

- **Downstream Power**: -6 to +15 dBmV
- **Upstream Power**: 35 to 48 dBmV

If your ISP uses different specs, you can modify the threshold values in the `check_specs()` method in `main.py`.

## Troubleshooting

### Connection Issues
- Ensure your modem is powered on and accessible at `192.168.100.1`
- Check your network connection
- Verify firewall allows local network access

### No Data Returned
- The modem API may be temporarily unavailable
- Try waiting a few seconds and running the command again
- Check if your modem supports the DOCSIS API endpoints

### Timeout Errors
- Modem is not responding within 10 seconds
- Try running with a single command (`ds`, `us`, or `status`) instead of `all`

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.