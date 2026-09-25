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

    def test_removes_a_stale_database_user_before_setup(self) -> None:
        install_script: str = (PROJECT_ROOT / "scripts" / "install").read_text()
        stale_user_check: int = install_script.index('ynh_psql_user_exists --user="$app"')
        database_cleanup: int = install_script.index("ynh_psql_remove_db")
        database_setup: int = install_script.index("ynh_psql_setup_db")

        self.assertLess(stale_user_check, database_cleanup)
        self.assertLess(database_cleanup, database_setup)

    def test_copies_readme_for_python_package_build(self) -> None:
        install_script: str = (PROJECT_ROOT / "scripts" / "install").read_text()

        self.assertIn('"$YNH_APP_BASEDIR/README.md"', install_script)

    def test_uses_systemd_commands_supported_by_yunohost_12(self) -> None:
        script_paths: tuple[Path, ...] = tuple((PROJECT_ROOT / "scripts").glob("*"))
        script_content: str = "\n".join(path.read_text() for path in script_paths)

        self.assertNotIn("ynh_systemctl", script_content)
        self.assertIn('systemctl start "$app"', script_content)

    def test_creates_the_virtual_environment_as_the_application_user(self) -> None:
        install_script: str = (PROJECT_ROOT / "scripts" / "install").read_text()
        ownership_fix: int = install_script.index('chown -R "$app":"$app" "$install_dir"')
        virtual_environment: int = install_script.index(
            'runuser -u "$app" -- python3 -m venv "$install_dir/venv"'
        )

        self.assertLess(ownership_fix, virtual_environment)

    def test_declares_yunohost_resources_and_single_instance_policy(self) -> None:
        manifest: str = (PROJECT_ROOT / "manifest.toml").read_text()

        self.assertIn("[resources]", manifest)
        self.assertIn("[resources.permissions]", manifest)
        self.assertIn('main.url = "/"', manifest)
        self.assertIn("multi_instance = false", manifest)

    def test_loads_common_settings_from_each_script_directory(self) -> None:
        script_directory: Path = PROJECT_ROOT / "scripts"
        script_paths: tuple[Path, ...] = tuple(script_directory.glob("*"))

        for script_path in script_paths:
            if script_path.name == "_common.sh":
                continue
            script_content: str = script_path.read_text()
            self.assertIn('source "$script_dir/_common.sh"', script_content)
