import asyncio
import httpx
import argparse
import json
import sys
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns

console = Console()

class HitronClient:
    def __init__(self, ip: str = "192.168.100.1"):
        self.ip = ip
        self.base_url = f"http://{ip}/data"
        self.semaphore = asyncio.Semaphore(2)
        
    async def fetch(self, endpoint: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/{endpoint}.asp"
        async with self.semaphore:
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    response = await client.get(url)
                    if response.status_code != 200: return []
                    data = json.loads(response.text.strip())
                    return data if isinstance(data, list) else [data]
                except: return []

    def check_specs(self, ds30, ds31, us30, us31):
        """Checks Midco specs: DS (-6 to 15), US (35 to 48)."""
        # Combine all DS power levels
        ds_powers = [float(ch.get('signalStrength', 0)) for ch in ds30]
        ds_powers += [float(ch.get('plcpower', 0)) for ch in ds31]
        
        # Combine all US power levels (with +6 for OFDMA)
        us_powers = [float(ch.get('signalStrength', 0)) for ch in us30]
        us_powers += [(float(ch.get('repPower1_6', 0)) + 6.0) for ch in us31]

        ds_min, ds_max = (min(ds_powers), max(ds_powers)) if ds_powers else (0, 0)
        us_min, us_max = (min(us_powers), max(us_powers)) if us_powers else (0, 0)

        ds_ok = -6 <= ds_min and ds_max <= 15
        us_ok = 35 <= us_min and us_max <= 48

        status = "[bold green]YES! 😎[/bold green]" if ds_ok and us_ok else "[bold red]NOPE ☹️[/bold red]"
        
        spec_report = (
            f"DS Power: {ds_min:+.1f} to {ds_max:+.1f} dBmV {'[green](OK)[/]' if ds_ok else '[red](BAD)[/]'}\n"
            f"US Power: {us_min:.1f} to {us_max:.1f} dBmV {'[green](OK)[/]' if us_ok else '[red](BAD)[/]'}\n"
            f"---------------------------\n"
            f"IS MODEM IN SPEC? {status}"
        )
        return Panel(spec_report, title="🏆 MIDCO SPEC CHECK", border_style="bold white")

    def render_ds(self, ds30, ds31):
        table = Table(title="Downstream Channels (All)", border_style="cyan")
        table.add_column("Type", style="dim")
        table.add_column("Ch")
        table.add_column("Freq (MHz)")
        table.add_column("Power (dBmV)")
        table.add_column("SNR (dB)")
        
        # Sort D3.0 by frequency
        ds30_sorted = sorted(ds30, key=lambda x: int(x.get('frequency', 0)))

        for ch in ds30_sorted:
            pwr = float(ch.get('signalStrength', 0))
            color = "green" if -6 <= pwr <= 15 else "bold red"
            freq = int(ch.get('frequency', 0)) / 1_000_000
            table.add_row("SC-QAM", ch.get('channelId'), f"{freq:.1f}", f"[{color}]{pwr:+.1f}[/]", ch.get('snr'))

        for ch in (ds31 or []):
            pwr = float(ch.get('plcpower', 0))
            color = "green" if -6 <= pwr <= 15 else "bold red"
            freq = float(ch.get('Subcarr0freqFreq', '0').strip()) / 1_000_000
            table.add_row("OFDM", "3.1", f"{freq:.1f}", f"[{color}]{pwr:+.1f}[/]", ch.get('SNR'), style="bold cyan")
        
        console.print(table)

    def render_us(self, us30, us31):
        table = Table(title="Upstream Channels (Sorted by Freq)", border_style="orange1")
        table.add_column("Type", style="dim")
        table.add_column("Ch")
        table.add_column("Freq (MHz)")
        table.add_column("Pwr (+6Adj)")

        # Create a unified list for sorting
        combined_us = []
        for ch in us30:
            combined_us.append({
                'type': 'ATDMA',
                'id': ch.get('channelId'),
                'freq': int(ch.get('frequency', 0)),
                'pwr': float(ch.get('signalStrength', 0))
            })
        for ch in (us31 or []):
            combined_us.append({
                'type': 'OFDMA',
                'id': ch.get('uschindex'),
                'freq': float(ch.get('frequency', 0)),
                'pwr': float(ch.get('repPower1_6', 0)) + 6.0
            })

        # Sort by frequency
        combined_us.sort(key=lambda x: x['freq'])

        for ch in combined_us:
            color = "green" if 35 <= ch['pwr'] <= 48 else "bold red"
            table.add_row(
                ch['type'], 
                str(ch['id']), 
                f"{ch['freq']/1e6:.1f}", 
                f"[{color}]{ch['pwr']:.2f}[/]"
            )
        console.print(table)

    def render_status(self, data):
        # Identity and Spec Check logic as before...
        sys_data = data.get("getSysInfo", [{}])[0]
        init = data.get("getCMInit", [{}])[0]
        spec_panel = self.check_specs(data.get("dsinfo", []), data.get("dsofdminfo", []), data.get("usinfo", []), data.get("usofdminfo", []))
        
        sys_info = (f"[bold cyan]MAC:[/bold cyan] {sys_data.get('rfMac')}\n"
                    f"[bold green]Uptime:[/bold green] {sys_data.get('systemUptime')}\n"
                    f"Traffic: {init.get('trafficStatus')}")
        
        console.print(Columns([Panel(sys_info, title="Identity"), spec_panel]))

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["ds", "us", "status", "all"])
    args = parser.parse_args()
    client = HitronClient()
    
    eps = ["dsinfo", "dsofdminfo", "usinfo", "usofdminfo", "getCMInit", "getLinkStatus", "getCmDocsisWan", "getSysInfo"]
    results = await asyncio.gather(*[client.fetch(ep) for ep in eps])
    data = dict(zip(eps, results))

    if args.cmd in ["status", "all"]: client.render_status(data)
    if args.cmd in ["ds", "all"]: client.render_ds(data["dsinfo"], data["dsofdminfo"])
    if args.cmd in ["us", "all"]: client.render_us(data["usinfo"], data["usofdminfo"])

if __name__ == "__main__":
    asyncio.run(main())