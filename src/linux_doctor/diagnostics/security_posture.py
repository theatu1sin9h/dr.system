"""Kernel Hardening, LSM, and OS Security Posture Diagnostic Engine.

Audits runtime kernel security flags without requiring root:
- LSM Status: AppArmor / SELinux
- ASLR (Address Space Layout Randomization)
- Kernel Pointer Protection (kptr_restrict)
- Dmesg Restriction (dmesg_restrict)
- Ptrace Scope (Yama LSM protection against process injection)
- Unprivileged eBPF restriction
- TCP SYN Cookies (SYN flood protection)
- IP Forwarding risk exposure
"""

import os
from pathlib import Path
from typing import Any, Dict, List
from linux_doctor.core.findings import DiagnosticFinding, FindingSeverity, ModuleResult


class KernelSecurityAuditor:
    """Safely audits Linux kernel security sysctl controls."""

    @staticmethod
    def _read_sysctl(path_str: str) -> str:
        p = Path(path_str)
        if p.exists() and p.is_file():
            try:
                return p.read_text().strip()
            except Exception:
                return "restricted"
        return "not_found"

    @classmethod
    def audit(cls) -> Dict[str, Any]:
        results: Dict[str, Any] = {}

        # 1. LSM (AppArmor / SELinux)
        apparmor_active = Path("/sys/kernel/security/apparmor").exists()
        selinux_active = Path("/sys/fs/selinux").exists()
        lsm_name = "None"
        if apparmor_active:
            lsm_name = "AppArmor (Enforcing)"
        elif selinux_active:
            lsm_name = "SELinux"
        results["lsm"] = lsm_name

        # 2. ASLR (randomize_va_space)
        # 0 = Disabled, 1 = Conservative, 2 = Full Randomization
        aslr_val = cls._read_sysctl("/proc/sys/kernel/randomize_va_space")
        aslr_status = "Disabled (Vulnerable)" if aslr_val == "0" else ("Full (Level 2 Active)" if aslr_val == "2" else f"Level {aslr_val}")
        results["aslr"] = aslr_status

        # 3. Kptr Restrict (kptr_restrict)
        # 0 = Exposed, 1 = Hidden to unpriv, 2 = Hidden to all
        kptr = cls._read_sysctl("/proc/sys/kernel/kptr_restrict")
        results["kptr_restrict"] = "Protected" if kptr in ("1", "2") else "Exposed (Kernel pointers leaked)"

        # 4. Dmesg Restrict (dmesg_restrict)
        dmesg_r = cls._read_sysctl("/proc/sys/kernel/dmesg_restrict")
        results["dmesg_restrict"] = "Hardened" if dmesg_r == "1" else "Unrestricted"

        # 5. Yama Ptrace Scope (process memory injection guard)
        # 0 = Classic ptrace, 1 = Restricted ptrace (same hierarchy), 2 = Admin only, 3 = No ptrace
        yama = cls._read_sysctl("/proc/sys/kernel/yama/ptrace_scope")
        yama_desc = {
            "0": "Permissive (Process injection risk)",
            "1": "Restricted (Standard Yama guard)",
            "2": "Admin Only",
            "3": "Locked Down",
        }.get(yama, yama)
        results["yama_ptrace"] = yama_desc

        # 6. Unprivileged BPF
        bpf_unpriv = cls._read_sysctl("/proc/sys/kernel/unprivileged_bpf_disabled")
        results["unprivileged_bpf"] = "Disabled (Hardened)" if bpf_unpriv in ("1", "2") else "Enabled"

        # 7. TCP SYN Cookies
        syncookies = cls._read_sysctl("/proc/sys/net/ipv4/tcp_syncookies")
        results["tcp_syncookies"] = "Active (SYN Flood Protected)" if syncookies == "1" else "Disabled"

        # 8. IP Forwarding (Router/MITM exposure)
        ip_fwd = cls._read_sysctl("/proc/sys/net/ipv4/ip_forward")
        results["ip_forwarding"] = "Disabled (Host Safe)" if ip_fwd == "0" else "Enabled (Routing Active)"

        return results


class SecurityPostureDiagnostic:
    """Diagnostic wrapper for Kernel Hardening and Security Flow."""

    @classmethod
    def run(cls) -> ModuleResult:
        findings: List[DiagnosticFinding] = []
        audit_data = KernelSecurityAuditor.audit()
        score = 100.0
        deductions_exp: List[str] = []

        # Evaluate ASLR
        if "Disabled" in audit_data.get("aslr", ""):
            findings.append(
                DiagnosticFinding(
                    id="sec_aslr_disabled",
                    title="ASLR (Address Space Randomization) Disabled",
                    severity=FindingSeverity.CRITICAL,
                    what_detected="randomize_va_space is set to 0. Memory layout is static and predictable.",
                    what_it_means="Memory-corruption exploits (ROP/buffer overflows) can execute without needing memory leaks.",
                    how_serious="High vulnerability to binary exploits.",
                    what_could_cause="Debugging flags or broken kernel boot parameters.",
                    what_user_should_do="Re-enable ASLR immediately: 'sudo sysctl -w kernel.randomize_va_space=2'.",
                    safe_next_step="Enable kernel ASLR protection.",
                    technical_details=audit_data,
                    is_hardware_degradation=False,
                    deduction_points=30.0,
                )
            )
            score -= 30.0
            deductions_exp.append("ASLR disabled (-30 pts)")

        # Evaluate LSM
        if audit_data.get("lsm") == "None":
            findings.append(
                DiagnosticFinding(
                    id="sec_no_lsm",
                    title="No Mandatory Access Control (MAC/LSM) Enforcing",
                    severity=FindingSeverity.WARNING,
                    what_detected="Neither AppArmor nor SELinux are actively confining system processes.",
                    what_it_means="Processes compromised by exploits can read any user file not blocked by basic DAC permissions.",
                    how_serious="Moderate.",
                    what_could_cause="Disabled in GRUB bootloader or minimal container environment.",
                    what_user_should_do="Enable AppArmor or SELinux.",
                    safe_next_step="Verify security module status in kernel configuration.",
                    technical_details=audit_data,
                    is_hardware_degradation=False,
                    deduction_points=15.0,
                )
            )
            score -= 15.0
            deductions_exp.append("No active LSM (AppArmor/SELinux) (-15 pts)")

        return ModuleResult(
            module_name="security_posture",
            display_name="Kernel Security & Hardening",
            status="passed" if score >= 85 else "warning",
            score=max(0.0, round(score, 1)),
            confidence=1.0,
            supported=True,
            metrics=audit_data,
            findings=findings,
            deductions_explanation=deductions_exp,
        )
