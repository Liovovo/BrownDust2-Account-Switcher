import sys
import json
import winreg
import locale
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, Menu


def get_app_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent


class AccountSwitcher:
    def __init__(self):
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
                messagebox.showwarning(
                    "提示" if hasattr(self, 'tr') else 'Tip', 
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
        
        self.root.destroy()
        self.__init__()

    def tr(self, key, *args):
        text = self.translations.get(key, key)
        if args:
            text = text.replace('{0}', str(args[0]))
            for i, arg in enumerate(args[1:], 1):
                text = text.replace(f'{{{i}}}', str(arg))
        return text

    def init_ui(self):
        self.root = tk.Tk()
        self.root.title(f"{self.tr('window_title')} - github.com/Liovovo/BrownDust2-Account-Switcher")
        
        width = 650
        height = 500
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(650, 500)

        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        title_frame.columnconfigure(0, weight=1)

        title_label = ttk.Label(title_frame, text=self.tr('account_list'), font=('', 12, 'bold'))
        title_label.grid(row=0, column=0, sticky=tk.W)

        self.lang_btn = ttk.Button(title_frame, text="EN" if self.lang == 'zh' else "中文", 
                                  command=self.switch_language, width=6)
        self.lang_btn.grid(row=0, column=1, sticky=tk.E)

        current_frame = ttk.Frame(main_frame)
        current_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        current_frame.columnconfigure(0, weight=1)

        self.current_account_label = ttk.Label(current_frame, text="", relief="solid", padding="8")
        self.current_account_label.grid(row=0, column=0, sticky=(tk.W, tk.E))

        self.btn_refresh_current = ttk.Button(current_frame, text="↻", width=3,
                                            command=self.refresh_current_account)
        self.btn_refresh_current.grid(row=0, column=1, padx=(5, 0))

        self.update_current_account_display()

        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        self.account_tree = ttk.Treeview(list_frame, columns=('info',), show='tree headings', height=15)
        self.account_tree.heading('#0', text=self.tr('account_name') if hasattr(self, 'tr') else 'Account Name')
        self.account_tree.heading('info', text=self.tr('account_info') if hasattr(self, 'tr') else 'Account Info')
        self.account_tree.column('#0', width=150)
        self.account_tree.column('info', width=450)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.account_tree.yview)
        self.account_tree.configure(yscrollcommand=scrollbar.set)
        
        self.account_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.account_tree.bind('<Double-1>', lambda e: self.load_account())
        self.account_tree.bind('<Button-3>', self.show_context_menu)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        self.btn_refresh_token = ttk.Button(btn_frame, text=self.tr('refresh_token'),
                                          command=self.refresh_token)
        self.btn_refresh_token.grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E))

        self.btn_save_new = ttk.Button(btn_frame, text=self.tr('save_current'),
                                     command=self.save_new_account)
        self.btn_save_new.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))

        self.btn_logout = ttk.Button(btn_frame, text=self.tr('logout'),
                                   command=self.logout_account)
        self.btn_logout.grid(row=0, column=2, padx=(5, 0), sticky=(tk.W, tk.E))

        for i in range(3):
            btn_frame.columnconfigure(i, weight=1)

        self.refresh_list()
        
        self.root.mainloop()

    def refresh_list(self):
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)
        
        for name, values in self.accounts.items():
            info = self.parse_account_info(values)
            
            info_parts = []
            if info['platform']:
                info_parts.append(info['platform'])
            if info['reg_nation']:
                info_parts.append(info['reg_nation'])
            if info['create_time']:
                info_parts.append(f"{self.tr('registered')}: {info['create_time']}")
            if info['token_time']:
                info_parts.append(f"{self.tr('token')}: {info['token_time']}")
            
            info_text = " | ".join(info_parts)
            
            self.account_tree.insert('', 'end', text=name, values=(info_text,), tags=(name,))

    def show_context_menu(self, event):
        item = self.account_tree.identify_row(event.y)
        if not item:
            return
        
        self.account_tree.selection_set(item)
        self.account_tree.focus(item)

        menu = Menu(self.root, tearoff=0)
        menu.add_command(label=self.tr('load_account'), command=self.load_account)
        menu.add_command(label=self.tr('overwrite_account'), command=self.overwrite_account)
        menu.add_separator()
        menu.add_command(label=self.tr('rename'), command=self.rename_account)
        menu.add_command(label=self.tr('delete'), command=self.delete_account)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
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
            self.current_account_label.config(text=f"{self.tr('current_login')}: {self.tr('not_logged_in')}")
            return
        
        current_token = None
        for key, value_data in current_values.items():
            if key.startswith('neon_access_token_h'):
                current_token = value_data.get('data', '') if isinstance(value_data, dict) else value_data
                current_token = current_token.rstrip('\x00')
                break
        
        if not current_token:
            self.current_account_label.config(text=f"{self.tr('current_login')}: {self.tr('not_logged_in')}")
            return
        
        current_parts = current_token.split('|')
        if len(current_parts) < 4:
            self.current_account_label.config(text=f"{self.tr('current_login')}: {self.tr('invalid_data')}")
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
            display_parts = [f"{matched_account}"]
        else:
            masked_id = self.get_masked_token_id(current_values)
            display_parts = [f"{masked_id}"]
        
        if info['platform']:
            display_parts.append(info['platform'])
        if info['reg_nation']:
            display_parts.append(info['reg_nation'])
        if info['create_time']:
            display_parts.append(f"{self.tr('registered')}: {info['create_time']}")
        if info['token_time']:
            display_parts.append(f"{self.tr('token')}: {info['token_time']}")
        
        display_text = f"{self.tr('current_login')}: {' | '.join(display_parts)}"
        
        self.current_account_label.config(text=display_text)

    def refresh_current_account(self):
        self.update_current_account_display()

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
                messagebox.showwarning(self.tr('error'), self.tr('registry_not_found'))
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
            messagebox.showwarning(self.tr('error'), self.tr('registry_not_found'))
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
            messagebox.showerror(self.tr('error'), self.tr('write_failed', str(e)))
            return False

    def save_new_account(self):
        values = self.read_registry_values()
        if not values:
            return

        name = simpledialog.askstring(self.tr('save_account_title'), self.tr('input_account_name'))
        if name:
            if name in self.accounts:
                if not messagebox.askyesno(self.tr('confirm'), self.tr('account_exists', name)):
                    return

            self.accounts[name] = values
            self.save_accounts()
            self.refresh_list()
            self.update_current_account_display()
            messagebox.showinfo(self.tr('success'), self.tr('account_saved', name))

    def overwrite_account(self):
        selection = self.account_tree.selection()
        if not selection:
            messagebox.showwarning(self.tr('tip'), self.tr('select_account_first'))
            return

        name = self.account_tree.item(selection[0])['text']
        values = self.read_registry_values()
        if not values:
            return

        if messagebox.askyesno(self.tr('confirm'), self.tr('overwrite_confirm', name)):
            self.accounts[name] = values
            self.save_accounts()
            self.refresh_list()
            self.update_current_account_display()
            messagebox.showinfo(self.tr('success'), self.tr('account_updated', name))

    def load_account(self):
        selection = self.account_tree.selection()
        if not selection:
            messagebox.showwarning(self.tr('tip'), self.tr('select_account_first'))
            return

        name = self.account_tree.item(selection[0])['text']
        values = self.accounts[name]

        if messagebox.askyesno(self.tr('confirm'), self.tr('load_confirm', name)):
            if self.write_registry_values(values):
                self.update_current_account_display()
                messagebox.showinfo(self.tr('success'), self.tr('account_loaded', name))

    def rename_account(self):
        selection = self.account_tree.selection()
        if not selection:
            messagebox.showwarning(self.tr('tip'), self.tr('select_rename'))
            return

        old_name = self.account_tree.item(selection[0])['text']
        new_name = simpledialog.askstring(self.tr('rename_account_title'), 
                                        self.tr('input_new_name'), initialvalue=old_name)
        
        if new_name and new_name != old_name:
            if new_name in self.accounts:
                messagebox.showwarning(self.tr('error'), self.tr('name_exists', new_name))
                return
            
            self.accounts[new_name] = self.accounts.pop(old_name)
            self.save_accounts()
            self.refresh_list()
            messagebox.showinfo(self.tr('success'), self.tr('renamed', new_name))

    def delete_account(self):
        selection = self.account_tree.selection()
        if not selection:
            messagebox.showwarning(self.tr('tip'), self.tr('select_delete'))
            return

        name = self.account_tree.item(selection[0])['text']
        if messagebox.askyesno(self.tr('confirm'), self.tr('delete_confirm', name)):
            del self.accounts[name]
            self.save_accounts()
            self.refresh_list()
            messagebox.showinfo(self.tr('success'), self.tr('account_deleted', name))

    def logout_account(self):
        if messagebox.askyesno(self.tr('confirm'), self.tr('logout_confirm')):
            registry_keys = self.get_registry_keys()
            empty_values = {key_name: {'data': '', 'type': winreg.REG_BINARY} for key_name in registry_keys.values()}
            if self.write_registry_values(empty_values):
                self.update_current_account_display()
                messagebox.showinfo(self.tr('success'), self.tr('logged_out'))

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
            messagebox.showwarning(self.tr('error'), self.tr('no_token'))
            return
        
        try:
            current_parts = current_token.split('|')
            if len(current_parts) < 4:
                messagebox.showwarning(self.tr('error'), self.tr('invalid_token'))
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
                if messagebox.askyesno(self.tr('confirm'), self.tr('matched_account', matched_account)):
                    self.accounts[matched_account] = current_values
                    self.save_accounts()
                    self.refresh_list()
                    self.update_current_account_display()
                    messagebox.showinfo(self.tr('success'), self.tr('token_updated', matched_account))
            else:
                masked_prefix = self.mask_prefix(current_prefix)
                messagebox.showinfo(self.tr('tip'), self.tr('no_match', masked_prefix))
        
        except Exception as e:
            messagebox.showerror(self.tr('error'), self.tr('refresh_failed', str(e)))

    def mask_prefix(self, prefix):
        parts = prefix.split('|')
        if len(parts) >= 1 and parts[0]:
            token_id = parts[0]
            if len(token_id) > 6:
                parts[0] = f"{token_id[:4]}***{token_id[-2:]}"
            return '|'.join(parts)
        return prefix


if __name__ == "__main__":
    app = AccountSwitcher()