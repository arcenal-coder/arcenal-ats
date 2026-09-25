from __future__ import annotations

from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class YunoHostInstallScriptTest(unittest.TestCase):
    def test_loads_database_password_before_systemd_rendering(self) -> None:
        install_script: str = (PROJECT_ROOT / "scripts" / "install").read_text()
        password_load: int = install_script.index('psqlpwd="$(ynh_app_setting_get')
        systemd_render: int = install_script.index("ynh_add_systemd_config")

        self.assertLess(password_load, systemd_render)

    def test_copies_readme_for_python_package_build(self) -> None:
        install_script: str = (PROJECT_ROOT / "scripts" / "install").read_text()

        self.assertIn('"$YNH_APP_BASEDIR/README.md"', install_script)
