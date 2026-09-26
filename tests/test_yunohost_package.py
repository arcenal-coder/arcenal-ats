from __future__ import annotations

from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class YunoHostInstallScriptTest(unittest.TestCase):
    def test_uses_the_database_resource_credentials(self) -> None:
        install_script: str = (PROJECT_ROOT / "scripts" / "install").read_text()
        manifest: str = (PROJECT_ROOT / "manifest.toml").read_text()

        self.assertIn('[resources.database]', manifest)
        self.assertIn('type = "postgresql"', manifest)
        self.assertIn('$db_user:$db_pwd@localhost/$db_name', install_script)
        self.assertNotIn("ynh_psql_setup_db", install_script)

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
        self.assertIn("[resources.ports]", manifest)
        self.assertIn("main.default = 8000", manifest)

    def test_uses_the_manifest_port_resource(self) -> None:
        install_script: str = (PROJECT_ROOT / "scripts" / "install").read_text()

        self.assertNotIn("ynh_find_port", install_script)

    def test_loads_common_settings_from_each_script_directory(self) -> None:
        script_directory: Path = PROJECT_ROOT / "scripts"
        script_paths: tuple[Path, ...] = tuple(script_directory.glob("*"))

        for script_path in script_paths:
            if script_path.name == "_common.sh":
                continue
            script_content: str = script_path.read_text()
            self.assertIn('source "$script_dir/_common.sh"', script_content)

    def test_uses_portable_positional_backup_arguments(self) -> None:
        backup_script: str = (PROJECT_ROOT / "scripts" / "backup").read_text()

        self.assertIn('ynh_backup "$install_dir" "apps/$app"', backup_script)
        self.assertIn('ynh_backup "$data_dir" "apps/$app-data"', backup_script)
        self.assertNotIn("--src", backup_script)
        self.assertNotIn("--dest", backup_script)

    def test_redirects_the_application_root_to_the_public_careers_page(self) -> None:
        nginx_config: str = (PROJECT_ROOT / "conf" / "nginx.conf").read_text()

        self.assertIn("location = __PATH__ {", nginx_config)
        self.assertEqual(nginx_config.count("auth_request off;"), 3)
        self.assertIn("return 302 __PATH__/recrutement;", nginx_config)
        self.assertIn("public-api/v1(?:/|$)", nginx_config)
        self.assertIn("public(?:/|$)", nginx_config)
        self.assertIn("auth_request off;", nginx_config)

    def test_upgrade_refreshes_runtime_and_proxy_configuration(self) -> None:
        upgrade_script: str = (PROJECT_ROOT / "scripts" / "upgrade").read_text()

        self.assertIn('cp -a "$YNH_APP_BASEDIR/src/." "$install_dir/src/"', upgrade_script)
        self.assertIn("--force-reinstall", upgrade_script)
        self.assertIn("ynh_config_add_nginx", upgrade_script)
        self.assertIn("ynh_config_add_systemd", upgrade_script)
        self.assertIn("nginx -t", upgrade_script)
        self.assertIn("systemctl reload nginx", upgrade_script)

    def test_uses_yunohost_21_configuration_helpers(self) -> None:
        install_script: str = (PROJECT_ROOT / "scripts" / "install").read_text()
        remove_script: str = (PROJECT_ROOT / "scripts" / "remove").read_text()
        restore_script: str = (PROJECT_ROOT / "scripts" / "restore").read_text()

        self.assertIn("ynh_config_add_nginx", install_script)
        self.assertIn("ynh_config_add_systemd", install_script)
        self.assertIn("ynh_config_remove_nginx", remove_script)
        self.assertIn("ynh_config_remove_systemd", remove_script)
        self.assertIn("ynh_restore_everything", restore_script)
