import sys
import json
import winreg
import locale
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QPushButton, QInputDialog, QMessageBox, QLabel, QListWidgetItem, QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QCursor


def get_app_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent


class AccountSwitcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.registry_path = r"SOFTWARE\Gamfs\BrownDust II"
        self.token_key_patterns = [
            "neon_access_token_h",
            "neon_auth_member_h"
        ]
        self.app_dir = get_app_dir()
        self.data_file = self.app_dir / "accounts.json"
        self.load_translations()
        self.accounts = self.load_accounts()
        self.init_ui()

    def get_registry_keys(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0, winreg.KEY_READ)
            keys = {}
            i = 0
            while True:
                try:
                    name = winreg.EnumValue(key, i)[0]
                    for pattern in self.token_key_patterns:
                        if name.startswith(pattern):
                            keys[pattern] = name
                            break
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
            return keys
        except FileNotFoundError:
            return {}

    def load_accounts(self):
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        return {}
                    data = json.loads(content)
                    self.config = data.get('_config', {})
                    accounts = {k: v for k, v in data.items() if k != '_config'}
                    return accounts
            except (json.JSONDecodeError, ValueError) as e:
                QMessageBox.warning(
                    None, self.tr('tip') if hasattr(self, 'tr') else 'Tip', 
                    self.tr('data_corrupted', str(e)) if hasattr(self, 'tr') else f'Data corrupted: {e}'
                )
                return {}
        return {}

    def save_accounts(self):
        data = {
            '_config': {
                **self.config,
                '_warning': 'This file contains sensitive account data. Do NOT share or upload publicly.'
            }
        }
        data.update(self.accounts)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_translations(self):
        trans_file = Path(__file__).parent / "translations.json"
        with open(trans_file, 'r', encoding='utf-8') as f:
            self.all_translations = json.load(f)
        
        self.config = {}
        saved_lang = None
        
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        self.config = data.get('_config', {})
                        saved_lang = self.config.get('language')
            except:
                pass
        
        if saved_lang and saved_lang in self.all_translations:
            self.lang = saved_lang
        else:
            try:
                import ctypes
                windll = ctypes.windll.kernel32
                lang_id = windll.GetUserDefaultUILanguage()
                if lang_id == 0x0804 or lang_id == 0x0404:
                    self.lang = 'zh'
                else:
                    self.lang = 'en'
            except:
                self.lang = 'en'
        
        self.translations = self.all_translations[self.lang]

    def switch_language(self):
        new_lang = 'en' if self.lang == 'zh' else 'zh'
        self.lang = new_lang
        self.translations = self.all_translations[self.lang]
        
        self.config['language'] = new_lang
        self.save_accounts()
        
        self.close()
        self.__init__()
        self.show()

    def tr(self, key, *args):
        text = self.translations.get(key, key)
        if args:
            text = text.replace('{0}', str(args[0]))
            for i, arg in enumerate(args[1:], 1):
                text = text.replace(f'{{{i}}}', str(arg))
        return text

    def init_ui(self):
        self.setWindowTitle(f"{self.tr('window_title')} - github.com/Liovovo/BrownDust2-Account-Switcher")
        self.setMinimumSize(650, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        title_layout = QHBoxLayout()
        title = QLabel(self.tr('account_list'))
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 8px 0;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        self.lang_btn = QPushButton("EN" if self.lang == 'zh' else "中文")
        self.lang_btn.setMaximumWidth(50)
        self.lang_btn.setStyleSheet("font-size: 11px; padding: 2px 5px;")
        self.lang_btn.clicked.connect(self.switch_language)
        title_layout.addWidget(self.lang_btn)
        
        layout.addLayout(title_layout)

        current_layout = QHBoxLayout()
        current_layout.setSpacing(8)
        
        self.current_account_label = QLabel()
        self.current_account_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                background-color: #f9f9f9;
            }
        """)
        self.current_account_label.setWordWrap(True)
        current_layout.addWidget(self.current_account_label, 1)
        
        self.btn_refresh_current = QPushButton("↻")
        self.btn_refresh_current.setMaximumWidth(40)
        self.btn_refresh_current.setMinimumHeight(36)
        self.btn_refresh_current.setStyleSheet("font-size: 18px;")
        self.btn_refresh_current.setToolTip(self.tr('refresh_token') if self.lang == 'zh' else 'Refresh')
        self.btn_refresh_current.clicked.connect(self.refresh_current_account)
        current_layout.addWidget(self.btn_refresh_current)
        
        layout.addLayout(current_layout)
        
        self.update_current_account_display()

        self.account_list = QListWidget()
        self.account_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
                outline: none;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #000;
                outline: none;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            QListWidget::item:focus {
                outline: none;
            }
        """)
        self.account_list.itemDoubleClicked.connect(self.load_account)
        self.account_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.account_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.account_list)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        self.btn_refresh_token = QPushButton(self.tr('refresh_token'))
        self.btn_refresh_token.setMinimumHeight(36)
        self.btn_refresh_token.clicked.connect(self.refresh_token)
        btn_layout.addWidget(self.btn_refresh_token)

        self.btn_save_new = QPushButton(self.tr('save_current'))
        self.btn_save_new.setMinimumHeight(36)
        self.btn_save_new.clicked.connect(self.save_new_account)
        btn_layout.addWidget(self.btn_save_new)

        self.btn_logout = QPushButton(self.tr('logout'))
        self.btn_logout.setMinimumHeight(36)
        self.btn_logout.clicked.connect(self.logout_account)
        btn_layout.addWidget(self.btn_logout)

        layout.addLayout(btn_layout)

        self.refresh_list()

    def refresh_list(self):
        self.account_list.clear()
        for name, values in self.accounts.items():
            info = self.parse_account_info(values)
            item = QListWidgetItem()
            
            display_text = f"{name}"
            if info['platform']:
                display_text += f"  |  {info['platform']}"
            if info['reg_nation']:
                display_text += f"  |  {info['reg_nation']}"
            if info['create_time']:
                display_text += f"  |  {self.tr('registered')}: {info['create_time']}"
            if info['token_time']:
                display_text += f"  |  {self.tr('token')}: {info['token_time']}"
            
            item.setText(display_text)
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.account_list.addItem(item)

    def show_context_menu(self, position):
        item = self.account_list.itemAt(position)
        if not item:
            return

        menu = QMenu()
        load_action = menu.addAction(self.tr('load_account'))
        overwrite_action = menu.addAction(self.tr('overwrite_account'))
        menu.addSeparator()
        rename_action = menu.addAction(self.tr('rename'))
        delete_action = menu.addAction(self.tr('delete'))

        action = menu.exec(QCursor.pos())
        
        if action == load_action:
            self.load_account()
        elif action == overwrite_action:
            self.overwrite_account()
        elif action == rename_action:
            self.rename_account()
        elif action == delete_action:
            self.delete_account()

    def parse_account_info(self, values):
        info = {'platform': '', 'create_time': '', 'token_time': '', 'reg_nation': ''}
        
        auth_member = None
        for key, value_data in values.items():
            if key.startswith('neon_auth_member_h'):
                auth_member = value_data.get('data', '') if isinstance(value_data, dict) else value_data
                break
        
        if auth_member:
            try:
                auth_member = auth_member.rstrip('\x00')
                data = json.loads(auth_member)
                
                reg_path = data.get('reg_path', '')
                if reg_path:
                    if reg_path.startswith('FIREBASE_'):
                        info['platform'] = reg_path.split('_', 1)[1]
                    else:
                        info['platform'] = reg_path
                
                reg_nation = data.get('reg_nation', '')
                if reg_nation:
                    info['reg_nation'] = reg_nation
                
                crt_dt = data.get('crt_dt')
                if crt_dt:
                    dt = datetime.fromtimestamp(crt_dt / 1000)
                    info['create_time'] = dt.strftime('%Y-%m-%d')
            except (json.JSONDecodeError, ValueError, KeyError):
                pass
        
        access_token = None
        for key, value_data in values.items():
            if key.startswith('neon_access_token_h'):
                access_token = value_data.get('data', '') if isinstance(value_data, dict) else value_data
                break
        
        if access_token:
            try:
                access_token = access_token.rstrip('\x00')
                parts = access_token.split('|')
                if len(parts) >= 6:
                    timestamp = int(parts[5])
                    token_dt = datetime.fromtimestamp(timestamp / 1000)
                    now = datetime.now()
                    delta = now - token_dt
                    
                    total_seconds = int(delta.total_seconds())
                    days = total_seconds // 86400
                    hours = (total_seconds % 86400) // 3600
                    minutes = (total_seconds % 3600) // 60
                    
                    if total_seconds < 3600:
                        if self.lang == 'zh':
                            info['token_time'] = f"{minutes}分钟前"
                        else:
                            info['token_time'] = f"{minutes}m ago"
                    elif total_seconds < 86400:
                        if self.lang == 'zh':
                            info['token_time'] = f"{hours}小时前"
                        else:
                            info['token_time'] = f"{hours}h ago"
                    else:
                        if self.lang == 'zh':
                            info['token_time'] = f"{days}天{hours}小时前"
                        else:
                            info['token_time'] = f"{days}d {hours}h ago"
            except (ValueError, IndexError):
                pass
        
        return info

    def normalize_account_data(self, values):
        for key, value in values.items():
            if key.startswith('neon_access_token_h'):
                token = value.rstrip('\x00')
                parts = token.split('|')
                if len(parts) >= 1 and parts[0]:
                    token_id = parts[0]
                    if len(token_id) > 6:
                        return f"{token_id[:4]}***{token_id[-2:]}"
                    return token_id
        return ""

    def update_current_account_display(self):
        current_values = self.read_registry_values()
        if not current_values:
            self.current_account_label.setText(f"{self.tr('current_login')}: {self.tr('not_logged_in')}")
            return
        
        current_token = None
        for key, value_data in current_values.items():
            if key.startswith('neon_access_token_h'):
                current_token = value_data.get('data', '') if isinstance(value_data, dict) else value_data
                current_token = current_token.rstrip('\x00')
                break
        
        if not current_token:
            self.current_account_label.setText(f"{self.tr('current_login')}: {self.tr('not_logged_in')}")
            return
        
        current_parts = current_token.split('|')
        if len(current_parts) < 4:
            self.current_account_label.setText(f"{self.tr('current_login')}: {self.tr('invalid_data')}")
            return
        
        current_prefix = '|'.join(current_parts[:4])
        
        matched_account = None
        for name, values in self.accounts.items():
            for key, value_data in values.items():
                if key.startswith('neon_access_token_h'):
                    saved_token = value_data.get('data', '') if isinstance(value_data, dict) else value_data
                    saved_token = saved_token.rstrip('\x00')
                    if saved_token:
                        saved_parts = saved_token.split('|')
                        if len(saved_parts) >= 4:
                            saved_prefix = '|'.join(saved_parts[:4])
                            if saved_prefix == current_prefix:
                                matched_account = name
                                break
            if matched_account:
                break
        
        info = self.parse_account_info(current_values)
        
        if matched_account:
            display_parts = [f"<b>{matched_account}</b>"]
        else:
            masked_id = self.get_masked_token_id(current_values)
            display_parts = [f"<b>{masked_id}</b>"]
        
        if info['platform']:
            display_parts.append(info['platform'])
        if info['reg_nation']:
            display_parts.append(info['reg_nation'])
        if info['create_time']:
            display_parts.append(f"{self.tr('registered')}: {info['create_time']}")
        if info['token_time']:
            display_parts.append(f"{self.tr('token')}: {info['token_time']}")
        
        display_text = f"{self.tr('current_login')}: {' | '.join(display_parts)}"
        
        self.current_account_label.setText(display_text)

    def refresh_current_account(self):
        self.update_current_account_display()

    def normalize_account_data(self, values):
        normalized = {}
        for key, value in values.items():
            for pattern in self.token_key_patterns:
                if key.startswith(pattern):
                    normalized[pattern] = value
                    break
        return normalized

    def get_masked_token_id(self, values):
        for key, value_data in values.items():
            if key.startswith('neon_access_token_h'):
                token = value_data.get('data', '') if isinstance(value_data, dict) else value_data
                token = token.rstrip('\x00')
                parts = token.split('|')
                if len(parts) >= 1 and parts[0]:
                    token_id = parts[0]
                    if len(token_id) > 6:
                        return f"{token_id[:4]}***{token_id[-2:]}"
                    return token_id
        return ""

    def read_registry_values(self):
        try:
            registry_keys = self.get_registry_keys()
            if not registry_keys:
                QMessageBox.warning(self, self.tr('error'), self.tr('registry_not_found'))
                return None
            
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0, winreg.KEY_READ)
            values = {}
            for pattern, key_name in registry_keys.items():
                try:
                    value, value_type = winreg.QueryValueEx(key, key_name)
                    if isinstance(value, bytes):
                        value_str = value.decode('utf-8', errors='ignore')
                    else:
                        value_str = str(value) if value else ""
                    values[key_name] = {'data': value_str, 'type': value_type}
                except FileNotFoundError:
                    values[key_name] = {'data': "", 'type': winreg.REG_BINARY}
            winreg.CloseKey(key)
            return values
        except FileNotFoundError:
            QMessageBox.warning(self, self.tr('error'), self.tr('registry_not_found'))
            return None

    def write_registry_values(self, values):
        try:
            registry_keys = self.get_registry_keys()
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0, winreg.KEY_WRITE)
            
            for saved_key, value_data in values.items():
                target_key = saved_key
                
                if isinstance(value_data, dict):
                    value_str = value_data.get('data', '')
                    value_type = value_data.get('type', winreg.REG_BINARY)
                else:
                    value_str = value_data
                    value_type = winreg.REG_BINARY
                
                for pattern in self.token_key_patterns:
                    if saved_key.startswith(pattern):
                        if pattern in registry_keys:
                            target_key = registry_keys[pattern]
                        break
                
                if value_type == winreg.REG_BINARY:
                    value_bytes = value_str.encode('utf-8') if value_str else b''
                    winreg.SetValueEx(key, target_key, 0, winreg.REG_BINARY, value_bytes)
                else:
                    winreg.SetValueEx(key, target_key, 0, value_type, value_str)
            
            winreg.CloseKey(key)
            return True
        except Exception as e:
            QMessageBox.critical(self, self.tr('error'), self.tr('write_failed', str(e)))
            return False

    def save_new_account(self):
        values = self.read_registry_values()
        if not values:
            return

        name, ok = QInputDialog.getText(self, self.tr('save_account_title'), self.tr('input_account_name'))
        if ok and name:
            if name in self.accounts:
                reply = QMessageBox.question(
                    self, self.tr('confirm'), self.tr('account_exists', name),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            self.accounts[name] = values
            self.save_accounts()
            self.refresh_list()
            self.update_current_account_display()
            QMessageBox.information(self, self.tr('success'), self.tr('account_saved', name))

    def overwrite_account(self):
        current_item = self.account_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, self.tr('tip'), self.tr('select_account_first'))
            return

        name = current_item.data(Qt.ItemDataRole.UserRole)
        values = self.read_registry_values()
        if not values:
            return

        reply = QMessageBox.question(
            self, self.tr('confirm'), self.tr('overwrite_confirm', name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.accounts[name] = values
            self.save_accounts()
            self.refresh_list()
            self.update_current_account_display()
            QMessageBox.information(self, self.tr('success'), self.tr('account_updated', name))

    def load_account(self):
        current_item = self.account_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, self.tr('tip'), self.tr('select_account_first'))
            return

        name = current_item.data(Qt.ItemDataRole.UserRole)
        values = self.accounts[name]

        reply = QMessageBox.question(
            self, self.tr('confirm'), self.tr('load_confirm', name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.write_registry_values(values):
                self.update_current_account_display()
                QMessageBox.information(self, self.tr('success'), self.tr('account_loaded', name))

    def rename_account(self):
        current_item = self.account_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, self.tr('tip'), self.tr('select_rename'))
            return

        old_name = current_item.data(Qt.ItemDataRole.UserRole)
        new_name, ok = QInputDialog.getText(self, self.tr('rename_account_title'), self.tr('input_new_name'), text=old_name)
        
        if ok and new_name:
            if new_name != old_name:
                if new_name in self.accounts:
                    QMessageBox.warning(self, self.tr('error'), self.tr('name_exists', new_name))
                    return
                
                self.accounts[new_name] = self.accounts.pop(old_name)
                self.save_accounts()
                self.refresh_list()
                QMessageBox.information(self, self.tr('success'), self.tr('renamed', new_name))

    def delete_account(self):
        current_item = self.account_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, self.tr('tip'), self.tr('select_delete'))
            return

        name = current_item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, self.tr('confirm'), self.tr('delete_confirm', name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            del self.accounts[name]
            self.save_accounts()
            self.refresh_list()
            QMessageBox.information(self, self.tr('success'), self.tr('account_deleted', name))

    def logout_account(self):
        reply = QMessageBox.question(
            self, self.tr('confirm'), self.tr('logout_confirm'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            registry_keys = self.get_registry_keys()
            empty_values = {key_name: {'data': '', 'type': winreg.REG_BINARY} for key_name in registry_keys.values()}
            if self.write_registry_values(empty_values):
                self.update_current_account_display()
                QMessageBox.information(self, self.tr('success'), self.tr('logged_out'))

    def refresh_token(self):
        current_values = self.read_registry_values()
        if not current_values:
            return
        
        current_token = None
        for key, value_data in current_values.items():
            if key.startswith('neon_access_token_h'):
                current_token = value_data.get('data', '') if isinstance(value_data, dict) else value_data
                current_token = current_token.rstrip('\x00')
                break
        
        if not current_token:
            QMessageBox.warning(self, self.tr('error'), self.tr('no_token'))
            return
        
        try:
            current_parts = current_token.split('|')
            if len(current_parts) < 4:
                QMessageBox.warning(self, self.tr('error'), self.tr('invalid_token'))
                return
            
            current_prefix = '|'.join(current_parts[:4])
            
            matched_account = None
            for name, values in self.accounts.items():
                for key, value_data in values.items():
                    if key.startswith('neon_access_token_h'):
                        saved_token = value_data.get('data', '') if isinstance(value_data, dict) else value_data
                        saved_token = saved_token.rstrip('\x00')
                        if saved_token:
                            saved_parts = saved_token.split('|')
                            if len(saved_parts) >= 4:
                                saved_prefix = '|'.join(saved_parts[:4])
                                if saved_prefix == current_prefix:
                                    matched_account = name
                                    break
                if matched_account:
                    break
            
            if matched_account:
                reply = QMessageBox.question(
                    self, self.tr('confirm'), 
                    self.tr('matched_account', matched_account),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.accounts[matched_account] = current_values
                    self.save_accounts()
                    self.refresh_list()
                    self.update_current_account_display()
                    QMessageBox.information(self, self.tr('success'), self.tr('token_updated', matched_account))
            else:
                masked_prefix = self.mask_prefix(current_prefix)
                QMessageBox.information(self, self.tr('tip'), self.tr('no_match', masked_prefix))
        
        except Exception as e:
            QMessageBox.critical(self, self.tr('error'), self.tr('refresh_failed', str(e)))

    def mask_prefix(self, prefix):
        parts = prefix.split('|')
        if len(parts) >= 1 and parts[0]:
            token_id = parts[0]
            if len(token_id) > 6:
                parts[0] = f"{token_id[:4]}***{token_id[-2:]}"
            return '|'.join(parts)
        return prefix


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AccountSwitcher()
    window.show()
    sys.exit(app.exec())
