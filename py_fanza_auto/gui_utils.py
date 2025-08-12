"""
GUI用ユーティリティ関数
"""
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Any, Optional
import json
import os

def show_info_message(title: str, message: str):
    """情報メッセージを表示"""
    messagebox.showinfo(title, message)

def show_error_message(title: str, message: str):
    """エラーメッセージを表示"""
    messagebox.showerror(title, message)

def show_warning_message(title: str, message: str):
    """警告メッセージを表示"""
    messagebox.showwarning(title, message)

def show_yes_no_dialog(title: str, message: str) -> bool:
    """はい/いいえダイアログを表示"""
    return messagebox.askyesno(title, message)

def show_ok_cancel_dialog(title: str, message: str) -> bool:
    """OK/キャンセルダイアログを表示"""
    return messagebox.askokcancel(title, message)

def validate_required_fields(fields: Dict[str, Any]) -> tuple[bool, str]:
    """必須フィールドの検証"""
    missing_fields = []
    
    for field_name, field_value in fields.items():
        if not field_value or (isinstance(field_value, str) and field_value.strip() == ""):
            missing_fields.append(field_name)
    
    if missing_fields:
        return False, f"以下のフィールドが必須です: {', '.join(missing_fields)}"
    
    return True, ""

def validate_url(url: str) -> bool:
    """URLの形式を検証"""
    if not url:
        return False
    
    # 基本的なURL形式チェック
    if not (url.startswith('http://') or url.startswith('https://')):
        return False
    
    # ドメイン部分の存在チェック
    if len(url.split('://')[1].split('/')[0]) == 0:
        return False
    
    return True

def validate_email(email: str) -> bool:
    """メールアドレスの形式を検証"""
    if not email:
        return False
    
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_numeric_range(value: str, min_val: float, max_val: float) -> bool:
    """数値範囲の検証"""
    try:
        num_val = float(value)
        return min_val <= num_val <= max_val
    except ValueError:
        return False

def convert_to_int(value: str, default: int = 0) -> int:
    """文字列を整数に変換"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def convert_to_float(value: str, default: float = 0.0) -> float:
    """文字列を浮動小数点数に変換"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def convert_to_bool(value: Any) -> bool:
    """値をブール値に変換"""
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    elif isinstance(value, (int, float)):
        return value != 0
    else:
        return False

def format_file_size(size_bytes: int) -> str:
    """ファイルサイズを人間が読みやすい形式に変換"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def format_duration(seconds: int) -> str:
    """秒数を人間が読みやすい形式に変換"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}分{remaining_seconds}秒"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60
        return f"{hours}時間{remaining_minutes}分{remaining_seconds}秒"

def create_tooltip(widget: tk.Widget, text: str):
    """ツールチップを作成"""
    def show_tooltip(event):
        tooltip = tk.Toplevel()
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        
        label = tk.Label(tooltip, text=text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1)
        label.pack()
        
        def hide_tooltip(event):
            tooltip.destroy()
        
        widget.bind('<Leave>', hide_tooltip)
        tooltip.bind('<Leave>', hide_tooltip)
    
    widget.bind('<Enter>', show_tooltip)

def center_window(window: tk.Tk):
    """ウィンドウを画面中央に配置"""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

def save_settings_to_file(settings: Dict[str, Any], filename: str) -> bool:
    """設定をファイルに保存"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"設定保存エラー: {e}")
        return False

def load_settings_from_file(filename: str) -> Optional[Dict[str, Any]]:
    """設定をファイルから読み込み"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"設定読み込みエラー: {e}")
    
    return None

def create_scrollable_frame(parent: tk.Widget) -> tuple[tk.Canvas, tk.Frame, tk.Scrollbar]:
    """スクロール可能なフレームを作成"""
    canvas = tk.Canvas(parent)
    scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    return canvas, scrollable_frame, scrollbar

def bind_mouse_wheel(widget: tk.Widget, canvas: tk.Canvas):
    """マウスホイールでスクロールを有効化"""
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    widget.bind("<MouseWheel>", _on_mousewheel)

def create_status_bar(parent: tk.Widget) -> tk.Label:
    """ステータスバーを作成"""
    status_bar = tk.Label(parent, text="準備完了", relief=tk.SUNKEN, anchor=tk.W)
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    return status_bar

def update_status_bar(status_bar: tk.Label, message: str):
    """ステータスバーのメッセージを更新"""
    status_bar.config(text=message)
    status_bar.update_idletasks()

def create_menu_bar(parent: tk.Tk) -> tk.Menu:
    """メニューバーを作成"""
    menubar = tk.Menu(parent)
    parent.config(menu=menubar)
    return menubar

def add_menu_item(menubar: tk.Menu, label: str, command=None, accelerator: str = ""):
    """メニューアイテムを追加"""
    menubar.add_command(label=label, command=command, accelerator=accelerator)

def add_separator(menubar: tk.Menu):
    """メニューセパレーターを追加"""
    menubar.add_separator()

def create_context_menu(parent: tk.Widget) -> tk.Menu:
    """コンテキストメニューを作成"""
    context_menu = tk.Menu(parent, tearoff=0)
    
    def show_context_menu(event):
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    parent.bind("<Button-3>", show_context_menu)
    return context_menu
